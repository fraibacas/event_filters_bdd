
from event_filters_test_helper import EventFiltersTestHelper

def before_all(context):
	context.zenoss_test_helper = EventFiltersTestHelper()
	context.zenoss_test_helper.init()
	context.archive = context.config.userdata.has_key("ARCHIVE")
	context.stop_before_finish = context.config.userdata.has_key("STOP_BEFORE_FINISH")

def after_all(context):
	context.zenoss_test_helper.shutdown()

def before_feature(context, feature):
	context.event_data = {} # { event_id: {event data}  }
	context.created_events = {}  # { event_id: uuid  }

def after_feature(context, feature):
	# after each run we should delete all the events that we created
	if context.stop_before_finish:
		print ("Press any key to continue")
		raw_input()
	for event_id, uuid in context.created_events.iteritems():
		context.zenoss_test_helper.delete_event(uuid, context.archive)

def before_scenario(context, scenario):

	context.current_scenario_data = {}
	context.current_filter = {}
	context.zep_response = {}

	if "Text Filters" in context.scenario.name:
	   # "| EVENT_ID | FIELD | VALUE | FILTER |"
	   context.current_scenario_data["event_id"] = context.scenario._row[0]
	   context.current_scenario_data["field"] = context.scenario._row[1]
	   context.current_scenario_data["value"] = context.scenario._row[2]
	   context.current_scenario_data["filter"] = context.scenario._row[3]
	elif any(x in context.scenario.name for x in ("OR filters", "NOT filters", "Sort Results")):
	     # "| EVENT_ID_1 | EVENT_ID_2 | FIELD | VALUE_1 | VALUE_2 |"
		context.current_scenario_data["event_id_1"] = context.scenario._row[0]
		context.current_scenario_data["event_id_2"] = context.scenario._row[1]
		context.current_scenario_data["field"] = context.scenario._row[2]
		context.current_scenario_data["value_1"] = context.scenario._row[3]
		context.current_scenario_data["value_2"] = context.scenario._row[4]
	elif any(x in context.scenario.name for x in ("Date Search", "Number Search" , "IP Address Search")):
		 # "| FIELD | FILTER | FOUND_EVENTS | NOT_FOUND_EVENTS |"
		context.current_scenario_data["field"] = context.scenario._row[0]
		context.current_scenario_data["filter"] = context.scenario._row[1]
		context.current_scenario_data["found_events"] = context.scenario._row[2]
		context.current_scenario_data["not_found_events"] = context.scenario._row[3]

def after_scenario(context, scenario):
	pass
