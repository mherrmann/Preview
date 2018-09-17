from fman import DirectoryPaneCommand, OK, CANCEL, show_file_open_dialog, \
	PLATFORM, load_json, show_alert, save_json
from fman.url import as_human_readable, splitscheme
from os.path import exists
from subprocess import Popen

class Preview(DirectoryPaneCommand):

	_PLATFORM_APPLICATIONS_FILTER = {
		'Mac': 'Applications (*.app)',
		'Windows': 'Applications (*.exe)',
		'Linux': 'Applications (*)'
	}
	_SETTINGS_FILE = 'Preview Settings.json'

	def __call__(self):
		if splitscheme(self.pane.get_path())[0] != 'file://':
			show_alert('Sorry, can only preview local files.')
		file_path = as_human_readable(self.pane.get_file_under_cursor())
		if not exists(file_path):
			show_alert('No file is selected!')
			return
		settings = load_json(self._SETTINGS_FILE, default={})
		viewer = settings.get('viewer', {})
		if not viewer:
			viewer = self._pick_viewer(
				'Viewer is currently not configured. Please pick one.'
			)
		if viewer:
			popen_kwargs = strformat_dict_values(viewer, {'file': file_path})
			try:
				self._preview(file_path, viewer)
			except FileNotFoundError:
				viewer = self._pick_viewer(
					'Could not find your Viewer. Please pick it again.'
				)
				if viewer:
					self._preview(file_path, viewer)
	def _preview(self, file_path, viewer):
		popen_kwargs = strformat_dict_values(viewer, {'file': file_path})
		Popen(**popen_kwargs)
	def _pick_viewer(self, message):
		choice = show_alert(message, OK | CANCEL, OK)
		if choice & OK:
			viewer_path = show_file_open_dialog(
				'Pick a viewer', self._get_applications_directory(),
				self._PLATFORM_APPLICATIONS_FILTER[PLATFORM]
			)
			if viewer_path:
				result = get_popen_kwargs_for_opening('{file}', viewer_path)
				settings = load_json(self._SETTINGS_FILE, default={})
				settings['viewer'] = result
				save_json(self._SETTINGS_FILE)
				return result
	def _get_applications_directory(self):
		if PLATFORM == 'Mac':
			return '/Applications'
		elif PLATFORM == 'Windows':
			result = r'c:\Program Files'
			if not exists(result):
				result = splitdrive(sys.executable)[0] + '\\'
			return result
		elif PLATFORM == 'Linux':
			return '/usr/bin'
		raise NotImplementedError(PLATFORM)

def get_popen_kwargs_for_opening(file_, with_):
	args = [with_, file_]
	if PLATFORM == 'Mac':
		args = ['/usr/bin/open', '-a'] + args
	return {'args': args}

def strformat_dict_values(dict_, replacements):
	result = {}
	def replace(value):
		if isinstance(value, str):
			return value.format(**replacements)
		return value
	for key, value in dict_.items():
		if isinstance(value, list):
			value = list(map(replace, value))
		else:
			value = replace(value)
		result[key] = value
	return result
