"""
Imports analysis data from a bnida JSON file to IDA
"""

import idc
import idautils
import ida_kernwin
import idaapi
import ida_segment
import ida_bytes
import ida_funcs
import ida_typeinf
import ida_idaapi
import json


def get_flag_from_type(typ):
    if typ in ['uint32_t', 'int32_t', 'DWORD', 'int']:
        return ida_bytes.dword_flag()
    elif typ in ['uint64_t', 'int64_t', 'LONG LONG']:
        return ida_bytes.qword_flag()
    elif typ in ['uint16_t', 'int16_t']:
        return ida_bytes.word_flag()
    else:
        return ida_bytes.byte_flag()


def adjust_addr(sections, addr):
    bn_section_start = None
    section_name = None
    for name, section in sections.items():
        if addr >= int(section['start']) and addr <= int(section['end']):
            bn_section_start = int(section['start'])
            section_name = name
            break

    # Make sure the section was found (this check should always pass)
    if section_name is None:
        print(
            'Section not found in bnida analysis data for addr: {:08x}'.format(
                addr))
        return None

    # Retrieve section start in IDA and adjust the addr
    ida_sections = idautils.Segments()
    for ea in ida_sections:
        segm = ida_segment.getseg(ea)
        if ida_segment.get_segm_name(segm) == section_name:
            return addr - bn_section_start + segm.start_ea

    print('Section not found - name:{} addr:{:08x}'.format(section_name, addr))
    return None


def import_functions(functions, sections):
    for addr in functions:
        addr = adjust_addr(sections, int(addr))
        if addr is None:
            continue

        if ida_funcs.get_func(addr):
            continue

        if not ida_funcs.add_func(addr):
            print('Failed to create function at offset:{:08x}'.format(addr))


def import_function_comments(comments, sections):
    for addr, comment in comments.items():
        addr = adjust_addr(sections, int(addr))
        if addr is None:
            continue

        func = ida_funcs.get_func(addr)
        if func is None:
            print('Failed to apply function comment at offset:{:08x}'.format(
                addr))
            continue

        ida_funcs.set_func_cmt(func, comment, False)


def import_line_comments(comments, sections):
    for addr, comment in comments.items():
        addr = adjust_addr(sections, int(addr))
        if addr is None:
            continue
        ida_bytes.set_cmt(addr, comment, 0)


def import_names(names, sections):
    for addr, name in names.items():
        addr = adjust_addr(sections, int(addr))
        if addr is None:
            continue

        if idc.get_name_ea_simple(name) == idaapi.BADADDR:
            # Invalid characters are silently sanitized with `_` here.
            idc.set_name(addr, name, idc.SN_NOCHECK)

def get_struc(struct_tid):
    tif = ida_typeinf.tinfo_t()
    if tif.get_type_by_tid(struct_tid):
        if tif.is_struct():
            return tif
    return ida_idaapi.BADADDR

def import_structures(structures):
    # curr_idx = ida_struct.get_last_struc_idx() + 1
    curr_idx = -1 # add_struc ignores index in ida 9
    for struct_name, struct_info in structures.items():
        # Create structure
        tid = idc.add_struc(curr_idx, struct_name, False)

        # Add members
        # struct = get_struc(tid)
        for member_name, member_info in struct_info['members'].items():
            flag = get_flag_from_type(member_info['type'])
            idc.add_struc_member(tid, member_name,
                                    member_info['offset'], flag, -1,
                                    member_info['size'])

        curr_idx += 1


def get_json(json_file):
    json_array = None
    if json_file is None:
        return None

    try:
        f = open(json_file, 'rb')
        json_array = json.load(f)
    except Exception as e:
        print('Failed to parse json file {} {}'.format(json_file, e))
    return json_array


def main(json_file):
    json_array = get_json(json_file)
    if not json_array:
        print('JSON file not specified')
        return

    print('Importing analysis data from {}'.format(json_file))
    import_functions(json_array['functions'], json_array['sections'])
    import_function_comments(json_array['func_comments'],
                             json_array['sections'])
    import_line_comments(json_array['line_comments'], json_array['sections'])
    import_names(json_array['names'], json_array['sections'])
    import_structures(json_array['structs'])
    print('Done importing analysis data')


if __name__ == '__main__':
    main(ida_kernwin.ask_file(0, '*.json', 'Import file name'))
