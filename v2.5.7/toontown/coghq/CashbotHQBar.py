import random
from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from direct.fsm import ClassicFSM
from direct.fsm import State
from toontown.battle import BattlePlace
from toontown.building import Elevator
from toontown.toonbase import ToontownGlobals
from toontown.hood import ZoneUtil
import FactoryExterior
DROP_POINTS = [(-7.978, 193.878, 0.325, -180, 0, 0),
 (-7.978, 193.878, 0.325, -180, 0, 0),
 (-7.978, 193.878, 0.325, -180, 0, 0),
 (-7.978, 193.878, 0.325, -180, 0, 0),
 (-7.978, 193.878, 0.325, -180, 0, 0),
 (-7.978, 193.878, 0.325, -180, 0, 0),
 (-7.978, 193.878, 0.325, -180, 0, 0)]

class CashbotHQBar(FactoryExterior.FactoryExterior):
    notify = DirectNotifyGlobal.directNotify.newCategory('CashbotHQBar')

    def __init__(self, loader, parentFSM, doneEvent):
        FactoryExterior.FactoryExterior.__init__(self, loader, parentFSM, doneEvent)
        self.elevatorDoneEvent = 'elevatorDone'
        self.trains = None
        self.fsm.addState(State.State('walk', self.enterWalk, self.exitWalk, ['elevator',
         'stickerBook',
         'teleportOut',
         'tunnelOut',
         'DFA',
         'doorOut',
         'died',
         'stopped',
         'WaitForBattle',
         'battle',
         'squished',
         'stopped']))
        self.fsm.addState(State.State('elevator', self.enterElevator, self.exitElevator, ['walk']))
        state = self.fsm.getStateNamed('walk')
        state.addTransition('elevator')
        return

    def enterTeleportIn(self, requestStatus):
        dropPoint = random.choice(DROP_POINTS)
        base.localAvatar.setPosHpr(dropPoint[0], dropPoint[1], dropPoint[2], dropPoint[3], dropPoint[4], dropPoint[5])
        self.barMusic = base.loader.loadMusic('phase_14.5/audio/bgm/CBHQ_bar.ogg')
        base.playMusic(self.barMusic, looping=1, volume=1)
        BattlePlace.BattlePlace.enterTeleportIn(self, requestStatus)

    def teleportInDone(self):
        BattlePlace.BattlePlace.teleportInDone(self)

    def enterElevator(self, distElevator, skipDFABoard=0):
        self.accept(self.elevatorDoneEvent, self.handleElevatorDone)
        self.elevator = Elevator.Elevator(self.fsm.getStateNamed('elevator'), self.elevatorDoneEvent, distElevator)
        if skipDFABoard:
            self.elevator.skipDFABoard = 1
        distElevator.elevatorFSM = self.elevator
        self.elevator.setReverseBoardingCamera(True)
        self.elevator.load()
        self.elevator.enter()

    def exitElevator(self):
        self.ignore(self.elevatorDoneEvent)
        self.elevator.unload()
        self.elevator.exit()
        del self.elevator

    def detectedElevatorCollision(self, distElevator):
        if self.fsm.getCurrentState().getName() == 'walk':
            self.fsm.request('elevator', [distElevator])

    def handleElevatorDone(self, doneStatus):
        self.notify.debug('handling elevator done event')
        where = doneStatus['where']
        if where == 'reject':
            if hasattr(base.localAvatar, 'elevatorNotifier') and base.localAvatar.elevatorNotifier.isNotifierOpen():
                pass
            else:
                self.fsm.request('walk')
        else:
            if where == 'exit':
                self.fsm.request('walk')
            else:
                if where == 'factoryExterior':
                    self.doneStatus = doneStatus
                    messenger.send(self.doneEvent)
                else:
                    self.notify.error('Unknown mode: ' + where + ' in handleElevatorDone')