"""
The Config module (for specifying the fuzzing configurations)
"""
# Tool Description
__description__ = "Criticality-guided simulation-based fuzzing for apollo"

# Tool Version
__version__ = "1.0.0"

# Tool Name
__prog__ = "viohawk"

# Simulation Config
SIM_SENSOR_CONF = "d7cbe8ec-9577-4a02-ba8b-441000552ae3"

# Mutate Probability
PROB_PedestrianVariant = 30
PROB_PedestrianPisition = 30
PROB_PedestrianSpeed = 50
PROB_TrafficConePosition = 30
PROB_WeatherRain = 30
PROB_WeatherFog = 30
PROB_WeatherWetness = 30
PROB_WeatherCloudiness = 30
PROB_TimeMonth = 30
PROB_TimeDay = 30
PROB_TimeHour = 30
PROB_TimeMinute = 30
PROB_TimeSecond = 30
PROB_NPCVariant = 30
PROB_NPCColor = 30
PROB_NPCPosition = 30
PROB_NPCWPSpeed = 50
PROB_NPCAdd = 30
PROB_NPCDelete = 30
PROB_NPCMaxSpeed = 30
PROB_TrafficLightState = 30
PROB_TrafficLightValue = 30
PROB_TrafficConeAdd = 0
PROB_TrafficConeDelete = 30
MAX_NPCAddCount = 10
MAX_NPCWPSpeed = 10
MAX_NPCMaxSpeed = 10
MAX_TrafficConeAddCount = 10
MAX_NPCDistance = 20
MIN_NPCDistance = 9
