from toontown.building import DistributedToonInteriorAI

class DistributedPizzeriaInteriorAI(DistributedToonInteriorAI.DistributedToonInteriorAI):

    def __init__(self, block, air, zoneId, building):
        DistributedToonInteriorAI.DistributedToonInteriorAI.__init__(self, block, air, zoneId, building)