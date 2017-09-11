from fman import DirectoryPaneCommand, OK, CANCEL, show_file_open_dialog, \
	PLATFORM, load_json, show_alert, save_json
from os.path import exists
from subprocess import Popen

class Preview(DirectoryPaneCommand):
	_PLATFORM_APPLICATIONS_FILTER = {
		'Mac': 'Applications (*.app)',
		'Windows': 'Applications (*.exe)',
		'Linux': 'Applications (*)'
	}
	def __call__(self):
		file_path = self.pane.get_file_under_cursor()
		if not exists(file_path):
			show_alert('No file is selected!')
			return
		settings = load_json('Preview Settings.json', default={})
		viewer = settings.get('viewer', {})
		if not viewer:
			choice = show_alert(
				'Viewer is currently not configured. Please pick one.',
				OK | CANCEL, OK
			)
			if choice & OK:
				viewer_path = show_file_open_dialog(
					'Pick a viewer', self._get_applications_directory(),
					self._PLATFORM_APPLICATIONS_FILTER[PLATFORM]
				)
				if viewer_path:
					viewer = get_popen_kwargs_for_opening('{file}', viewer_path)
					settings['viewer'] = viewer
					save_json('Preview Settings.json')
		if viewer:
			popen_kwargs = strformat_dict_values(viewer, {'file': file_path})
			Popen(**popen_kwargs)
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