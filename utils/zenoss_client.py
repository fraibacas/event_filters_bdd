import json
import urllib2
from urllib import urlencode

def _buildOpener():
    cookieHandler = urllib2.HTTPCookieProcessor()
    return urllib2.build_opener(cookieHandler)

class ZenossClient(object):
	""" Proxy to interact with Zenoss """
	def __init__(self):
		""" """
		self.session = None
		self.user = ""
		self.password = ""
		self.zenoss_url = ""
		self._opener = _buildOpener()

	def init(self, config):
		""" """
		self.zenoss_url = config.get("zenoss_url")
		self.user = config.get("zenoss_user")
		self.password = config.get("zenoss_password")

		if 'http' not in self.zenoss_url:
			self.BASE_URL = 'http://{0}/zport'.format(self.zenoss_url)
		else:
			self.BASE_URL = '{0}/zport'.format(self.zenoss_url)
		self.AUTH_URL = '{0}/acl_users/cookieAuthHelper/login'.format(self.BASE_URL)
		self.EVENTS_ROUTER_URL = '{0}/dmd/Events/evconsole_router'.format(self.BASE_URL)
		self.DASHBOARD_URL = '{0}/dmd/Dashboard'.format(self.BASE_URL)
		self.login()

	def shutdown(self):
		pass 

	def login(self):
		success = False
		data = { "__ac_name": self.user, "__ac_password": self.password}
		req = urllib2.Request(self.AUTH_URL, data=urlencode(data))
		try:
			f = self._opener.open(req)
		except urllib2.URLError as ex:
			print "%s: %s" % (self.AUTH_URL, ex)
			return success
		login_resp = f.read()
		f.close()
		title = login_resp.split('<title>')[1].split('</title>')[0]
		if "Dashboard" in title:
			success = True
		else:
			self.session = None
		return success

	def _build_request_body(self, request_info):
		body = request_info.get('body')
		if not body:
			body = {}
			body = { 'type':'rpc', 'tid':185, }
			body["action"] = request_info['action']
			body["method"] = request_info['method']

			page = request_info.get('page', 1)
			sort = request_info.get('sort', 'lastTime')
			limit = request_info.get('limit', 200)
			start = (page -1)*limit
			data = {"uid": "/zport/dmd", "page": page, "limit": limit, "start": start, "sort": sort, "dir":"DESC"}

			params = request_info.get('params')
			if not params:
				params = {}
				owner_id = request_info.get('user')
				device = request_info.get('device')
				event_state = request_info.get('event_state', [0, 1, 2, 3, 4, 5, 6])
				event_severty = request_info.get('event_severity', [0, 1, 2, 3, 4, 5])
				incident = request_info.get('incident')
				event_class = request_info.get('event_class')
				evid = request_info.get('evid')

				summary = request_info.get('summary')
				params['eventState'] = event_state
				params['severity'] = event_severty
				if owner_id:
					params['ownerid'] = owner_id
				if device:
					params['device'] = device
				if summary:
					params['summary'] = summary
				if incident:
					params['zenoss.IncidentManagement.number'] = incident
				if event_class:
					params["eventClass"] = event_class
				if evid:
					params["evid"] = evid

			default_keys = [ "ownerid", "eventState", "severity", "device", "component", "eventClass", 
						     "summary", "firstTime", "lastTime", "count", "evid", "eventClassKey", "message" ]

			data["params"] = params
			data["keys"] = request_info.get('keys', default_keys)
			if request_info.get('sort') and request_info.get('dir'):
				data['sort'] = request_info.get('sort')
				data['dir'] = request_info.get('dir')
			body["data"] = [data]

		return body

	def _send_request(self, url, body):
		"""
		Sends request using requests module
		"""
		headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
		connected = False
		if not self.session:
			connected = self.login()
		request = urllib2.Request(url, data=json.dumps(body), headers=headers)
		response = self._opener.open(request)
		response = json.loads(response.read())
		return response["result"]

	def send_event_filter_request(self, request_info={}, archive=False):
		"""
		returns a dict with keys [u'totalCount', u'events', u'success', u'asof']
		"""
		url = self.EVENTS_ROUTER_URL
		request_info['action'] = 'EventsRouter'
		request_info['method'] = 'query'
		if archive:
			request_info['event_state'] = [3, 4, 6]
			request_info['method'] = 'queryArchive'

		body = self._build_request_body(request_info)
		response = self._send_request(url, body)
		return response

	def send_event_creation_request(self, event):
		url = self.EVENTS_ROUTER_URL
		body = {}
		body['type'] = 'rpc'
		body['tid'] = 222
		body['action'] = 'EventsRouter'
		body['method'] = 'add_event'

		body['data'] = [event]
		response = self._send_request(url, body)
		return response
	
	def acknowledge_event(self, uuid):
		url = self.EVENTS_ROUTER_URL
		body = {}
		body['type'] = 'rpc'
		body['tid'] = 223
		body['action'] = 'EventsRouter'
		body['method'] = 'acknowledge'
		body["data"] = [ { "evids":[uuid],  } ]
		response = self._send_request(url, body)
		return response

	def reopen_event(self, uuid):
		url = self.EVENTS_ROUTER_URL
		body = {}
		body['type'] = 'rpc'
		body['tid'] = 223
		body['action'] = 'EventsRouter'
		body['method'] = 'reopen'
		body["data"] = [ { "evids":[uuid],  } ]
		response = self._send_request(url, body)
		return response

	def close_event(self, uuid):
		url = self.EVENTS_ROUTER_URL
		body = {}
		body['type'] = 'rpc'
		body['tid'] = 223
		body['action'] = 'EventsRouter'
		body['method'] = 'close'
		body["data"] = [ { "evids":[uuid],  } ]
		response = self._send_request(url, body)
		return response
