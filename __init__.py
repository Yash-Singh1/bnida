from binaryninja import PluginCommand
from .binja import import_data_in_background, export_data_in_background

PluginCommand.register('bnida\\Import analysis data',
                       'Import analysis data from bnida JSON file',
                       import_data_in_background)

PluginCommand.register('bnida\\Export analysis data',
                       'Export analysis data to a bnida JSON file',
                       export_data_in_background)
