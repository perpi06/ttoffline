from SpecImports import *
LobbyParent = 10014
BoilerParent = 10030
PipeLeftParent = 10023
PipeRightParent = 10032
OilParent = 10034
ControlParent = 10037
DuctParent = 10036
CenterSiloBattleCellParent = 10064
CenterSiloParent = 20095
CenterSiloOutsideParent = 26900
SigRoomParent = 20058
WestSiloParent = 20094
WestSiloBattleCellParent = 10047
EastSiloParent = 20096
EastSiloBattleCellParent = 10068
LobbyCell = 0
BoilerCell = 1
PipeLeftCell = 2
PipeRightCell = 3
OilCell = 4
ControlCell = 5
DuctCell = 6
CenterSiloCell = 7
SigRoomCell = 8
WestSiloCell = 9
EastSiloCell = 10
CenterSiloOutsideCell = 11
BattleCells = {LobbyCell: {'parentEntId': LobbyParent, 'pos': Point3(0, 0, 0)}, 
   BoilerCell: {'parentEntId': BoilerParent, 'pos': Point3(0, 0, 0)}, 
   OilCell: {'parentEntId': OilParent, 'pos': Point3(0, 0, 0)}, 
   ControlCell: {'parentEntId': ControlParent, 'pos': Point3(0, 0, 0)}, 
   CenterSiloCell: {'parentEntId': CenterSiloBattleCellParent, 'pos': Point3(0, 0, 0)}, 
   PipeLeftCell: {'parentEntId': PipeLeftParent, 'pos': Point3(0, 0, 0)}, 
   PipeRightCell: {'parentEntId': PipeRightParent, 'pos': Point3(0, 0, 0)}, 
   DuctCell: {'parentEntId': DuctParent, 'pos': Point3(0, 0, 0)}, 
   SigRoomCell: {'parentEntId': SigRoomParent, 'pos': Point3(0, 0, 0)}, 
   WestSiloCell: {'parentEntId': WestSiloBattleCellParent, 'pos': Point3(0, 0, 0)}, 
   EastSiloCell: {'parentEntId': EastSiloBattleCellParent, 'pos': Point3(-20, -10, 0)}, 
   CenterSiloOutsideCell: {'parentEntId': CenterSiloOutsideParent, 'pos': Point3(-20, -10, 0)}}
CogData = [
 {'type': 'nd', 'parentEntId': LobbyParent, 
    'boss': 0, 
    'level': 6, 
    'battleCell': LobbyCell, 
    'pos': Point3(0, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20078, 
    'skeleton': 0},
 {'type': 'nd', 'parentEntId': LobbyParent, 
    'boss': 0, 
    'level': 6, 
    'battleCell': LobbyCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20009, 
    'skeleton': 0},
 {'type': 'ms', 'parentEntId': LobbyParent, 
    'boss': 0, 
    'level': 7, 
    'battleCell': LobbyCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20079, 
    'skeleton': 0},
 {'type': 'cc', 'parentEntId': BoilerParent, 
    'boss': 0, 
    'level': 5, 
    'battleCell': BoilerCell, 
    'pos': Point3(0, 0, 0), 
    'h': 0, 
    'behavior': 'walk', 
    'path': 20076, 
    'skeleton': 0},
 {'type': 'nd', 'parentEntId': BoilerParent, 
    'boss': 0, 
    'level': 6, 
    'battleCell': BoilerCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'walk', 
    'path': 20077, 
    'skeleton': 0},
 {'type': 'tm', 'parentEntId': BoilerParent, 
    'boss': 0, 
    'level': 7, 
    'battleCell': BoilerCell, 
    'pos': Point3(0, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': None, 
    'skeleton': 0},
 {'type': 'ms', 'parentEntId': OilParent, 
    'boss': 0, 
    'level': 5, 
    'battleCell': OilCell, 
    'pos': Point3(-10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 60133, 
    'skeleton': 0},
 {'type': 'ms', 'parentEntId': OilParent, 
    'boss': 0, 
    'level': 6, 
    'battleCell': OilCell, 
    'pos': Point3(0, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 60134, 
    'skeleton': 0},
 {'type': 'ms', 'parentEntId': OilParent, 
    'boss': 0, 
    'level': 6, 
    'battleCell': OilCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 60135, 
    'skeleton': 0},
 {'type': 'tm', 'parentEntId': ControlParent, 
    'boss': 0, 
    'level': 6, 
    'battleCell': ControlCell, 
    'pos': Point3(-10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20039, 
    'skeleton': 1},
 {'type': 'ms', 'parentEntId': ControlParent, 
    'boss': 0, 
    'level': 7, 
    'battleCell': ControlCell, 
    'pos': Point3(0, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20049, 
    'skeleton': 1},
 {'type': 'tm', 'parentEntId': ControlParent, 
    'boss': 0, 
    'level': 6, 
    'battleCell': ControlCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20075, 
    'skeleton': 1},
 {'type': 'le', 'parentEntId': CenterSiloOutsideParent, 
    'boss': 0, 
    'level': 10, 
    'battleCell': CenterSiloOutsideCell, 
    'pos': Point3(-10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20103, 
    'forceType': True, 
    'skeleton': 0},
 {'type': 'ms', 'parentEntId': CenterSiloParent, 
    'boss': 0, 
    'level': 7, 
    'battleCell': CenterSiloCell, 
    'pos': Point3(-10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20103, 
    'skeleton': 0},
 {'type': 'sf', 'parentEntId': CenterSiloParent, 
    'boss': 1, 
    'level': 50, 
    'battleCell': CenterSiloCell, 
    'pos': Point3(0, 0, 0), 
    'h': 180, 
    'behavior': 'stand', 
    'path': None, 
    'forceType': True, 
    'skeleton': 1},
 {'type': 'gh', 'parentEntId': CenterSiloParent, 
    'boss': 0, 
    'level': 7, 
    'battleCell': CenterSiloCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20104, 
    'skeleton': 0},
 {'type': 'mh', 'parentEntId': CenterSiloParent, 
    'boss': 0, 
    'level': 11, 
    'battleCell': CenterSiloCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20105, 
    'forceType': True, 
    'skeleton': 0},
 {'type': 'm', 'parentEntId': WestSiloParent, 
    'boss': 0, 
    'level': 10, 
    'battleCell': WestSiloCell, 
    'pos': Point3(-10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20097, 
    'skeleton': 0},
 {'type': 'gh', 'parentEntId': WestSiloParent, 
    'boss': 0, 
    'level': 7, 
    'battleCell': WestSiloCell, 
    'pos': Point3(0, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20098, 
    'skeleton': 0},
 {'type': 'm', 'parentEntId': WestSiloParent, 
    'boss': 0, 
    'level': 9, 
    'battleCell': WestSiloCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20099, 
    'skeleton': 0},
 {'type': 'ms', 'parentEntId': EastSiloParent, 
    'boss': 0, 
    'level': 7, 
    'battleCell': EastSiloCell, 
    'pos': Point3(-10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20100, 
    'skeleton': 0},
 {'type': 'gh', 'parentEntId': EastSiloParent, 
    'boss': 0, 
    'level': 8, 
    'battleCell': EastSiloCell, 
    'pos': Point3(0, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20101, 
    'skeleton': 0},
 {'type': 'm', 'parentEntId': EastSiloParent, 
    'boss': 0, 
    'level': 11, 
    'battleCell': EastSiloCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20102, 
    'skeleton': 0},
 {'type': 'ols', 'parentEntId': PipeLeftParent, 
    'boss': 0, 
    'level': 11, 
    'battleCell': PipeLeftCell, 
    'pos': Point3(-10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20109, 
    'forceType': True, 
    'skeleton': 1},
 {'type': 'tm', 'parentEntId': PipeRightParent, 
    'boss': 0, 
    'level': 5, 
    'battleCell': PipeRightCell, 
    'pos': Point3(-10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20106, 
    'skeleton': 1},
 {'type': 'tm', 'parentEntId': PipeRightParent, 
    'boss': 0, 
    'level': 6, 
    'battleCell': PipeRightCell, 
    'pos': Point3(0, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20107, 
    'skeleton': 1},
 {'type': 'tm', 'parentEntId': PipeRightParent, 
    'boss': 0, 
    'level': 5, 
    'battleCell': PipeRightCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20108, 
    'skeleton': 1},
 {'type': 'ms', 'parentEntId': DuctParent, 
    'boss': 0, 
    'level': 4, 
    'battleCell': DuctCell, 
    'pos': Point3(0, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20038, 
    'skeleton': 0},
 {'type': 'tm', 'parentEntId': DuctParent, 
    'boss': 0, 
    'level': 6, 
    'battleCell': DuctCell, 
    'pos': Point3(10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20067, 
    'skeleton': 0},
 {'type': 'tm', 'parentEntId': DuctParent, 
    'boss': 0, 
    'level': 5, 
    'battleCell': DuctCell, 
    'pos': Point3(-10, 0, 0), 
    'h': 0, 
    'behavior': 'chase', 
    'path': 20068, 
    'skeleton': 0},
 {'type': 'tm', 'parentEntId': SigRoomParent, 
    'boss': 0, 
    'level': 5, 
    'battleCell': SigRoomCell, 
    'pos': Point3(5, -10.75, 0), 
    'h': -90, 
    'behavior': 'stand', 
    'path': None, 
    'skeleton': 0},
 {'type': 'tm', 'parentEntId': SigRoomParent, 
    'boss': 0, 
    'level': 6, 
    'battleCell': SigRoomCell, 
    'pos': Point3(5, -3.25, 0), 
    'h': -90, 
    'behavior': 'stand', 
    'path': None, 
    'skeleton': 0},
 {'type': 'tm', 'parentEntId': SigRoomParent, 
    'boss': 0, 
    'level': 5, 
    'battleCell': SigRoomCell, 
    'pos': Point3(5, 3.25, 0), 
    'h': -90, 
    'behavior': 'stand', 
    'path': None, 
    'skeleton': 0},
 {'type': 'm', 'parentEntId': SigRoomParent, 
    'boss': 0, 
    'level': 7, 
    'battleCell': SigRoomCell, 
    'pos': Point3(5, 10.75, 0), 
    'h': -90, 
    'behavior': 'stand', 
    'path': None, 
    'skeleton': 0}]
ReserveCogData = []