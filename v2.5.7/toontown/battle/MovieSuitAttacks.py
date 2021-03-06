from toontown.toonbase.ToontownGlobals import *
from SuitBattleGlobals import *
from direct.interval.IntervalGlobal import *
from BattleBase import *
from BattleProps import *
from toontown.suit.SuitDNA import *
from BattleBase import *
from BattleSounds import *
import MovieCamera
from direct.directnotify import DirectNotifyGlobal
import MovieUtil
from direct.particles import ParticleEffect
import BattleParticles
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toon import Toon
from toontown.effects import DustCloud
from otp.nametag.NametagConstants import *
from otp.nametag import NametagGlobals
from otp.otpbase import PythonUtil
from direct.actor.Actor import Actor
from direct.task import Task
notify = DirectNotifyGlobal.directNotify.newCategory('MovieSuitAttacks')
hitSoundFiles = ('AA_tart_only.ogg', 'AA_slice_only.ogg', 'AA_slice_only.ogg', 'AA_slice_only.ogg',
                 'AA_slice_only.ogg', 'AA_wholepie_only.ogg', 'AA_wholepie_only.ogg')

def __propPreflight(props, suit, toon, battle):
    prop = props[0]
    toon.update(0)
    prop.wrtReparentTo(battle)
    props[1].reparentTo(hidden)
    for ci in range(prop.getNumChildren()):
        prop.getChild(ci).setHpr(0, -90, 0)

    targetPnt = MovieUtil.avatarFacePoint(suit, other=battle)
    prop.lookAt(targetPnt)


def __getSoundTrack(level, hitSuit, tPieLeavesHand, node=None):
    throwSound = globalBattleSoundCache.getSound('AA_pie_throw_only.ogg')
    throwTrack = Sequence(Wait(2.6), SoundInterval(throwSound, node=node))
    if hitSuit:
        hitSound = globalBattleSoundCache.getSound('AA_wholepie_only.ogg')
        hitTrack = Sequence(Wait(tPieLeavesHand), SoundInterval(hitSound, node=node))
        return Parallel(throwTrack, hitTrack)
    return throwTrack


def __billboardProp(prop):
    scale = prop.getScale()
    prop.setBillboardPointWorld()
    prop.setScale(scale)


def __suitMissPoint(suit, other=render):
    pnt = suit.getPos(other)
    pnt.setZ(pnt[2] + suit.getHeight() * 1.3)
    return pnt


def __piePreMiss(missDict, pie, suitPoint, other=render):
    ratioMissToHit = 1.5
    missDict['pie'] = pie
    missDict['startScale'] = pie.getScale()
    missDict['startPos'] = pie.getPos(other)
    v = Vec3(suitPoint - missDict['startPos'])
    endPos = missDict['startPos'] + v * ratioMissToHit
    missDict['endPos'] = endPos


def __pieMissLerpCallback(t, missDict):
    tPieShrink = 0.7
    pie = missDict['pie']
    newPos = missDict['startPos'] * (1.0 - t) + missDict['endPos'] * t
    if t < tPieShrink:
        tScale = 0.0001
    else:
        tScale = (t - tPieShrink) / (1.0 - tPieShrink)
    newScale = missDict['startScale'] * max(1.0 - tScale, 0.01)
    pie.setPos(newPos)
    pie.setScale(newScale)


def __doDamage(toon, dmg, died):
    if dmg > 0 and toon.hp != None:
        toon.takeDamage(dmg)
    return


def __showProp(prop, parent, pos, hpr=None, scale=None):
    prop.reparentTo(parent)
    prop.setPos(pos)
    if hpr:
        prop.setHpr(hpr)
    if scale:
        prop.setScale(scale)


def __animProp(prop, propName, propType='actor'):
    if 'actor' == propType:
        prop.play(propName)
    else:
        if 'model' == propType:
            pass
        else:
            self.notify.error('No such propType as: %s' % propType)


def __suitFacePoint(suit, zOffset=0):
    pnt = suit.getPos()
    pnt.setZ(pnt[2] + suit.shoulderHeight + 0.3 + zOffset)
    return Point3(pnt)


def __toonFacePoint(toon, zOffset=0, parent=render):
    pnt = toon.getPos(parent)
    pnt.setZ(pnt[2] + toon.shoulderHeight + 0.3 + zOffset)
    return Point3(pnt)


def __toonTorsoPoint(toon, zOffset=0):
    pnt = toon.getPos()
    pnt.setZ(pnt[2] + toon.shoulderHeight - 0.2)
    return Point3(pnt)


def __toonGroundPoint(attack, toon, zOffset=0, parent=render):
    pnt = toon.getPos(parent)
    battle = attack['battle']
    pnt.setZ(battle.getZ(parent) + zOffset)
    return Point3(pnt)


def __toonGroundMissPoint(attack, prop, toon, zOffset=0):
    point = __toonMissPoint(prop, toon)
    battle = attack['battle']
    point.setZ(battle.getZ() + zOffset)
    return Point3(point)


def __toonMissPoint(prop, toon, yOffset=0, parent=None):
    if parent:
        p = __toonFacePoint(toon) - prop.getPos(parent)
    else:
        p = __toonFacePoint(toon) - prop.getPos()
    v = Vec3(p)
    baseDistance = v.length()
    v.normalize()
    if parent:
        endPos = prop.getPos(parent) + v * (baseDistance + 5 + yOffset)
    else:
        endPos = prop.getPos() + v * (baseDistance + 5 + yOffset)
    return Point3(endPos)


def __toonMissBehindPoint(toon, parent=render, offset=0):
    point = toon.getPos(parent)
    point.setY(point.getY() - 5 + offset)
    return point


def __throwBounceHitPoint(prop, toon):
    startPoint = prop.getPos()
    endPoint = __toonFacePoint(toon)
    return __throwBouncePoint(startPoint, endPoint)


def __throwBounceMissPoint(prop, toon):
    startPoint = prop.getPos()
    endPoint = __toonFacePoint(toon)
    return __throwBouncePoint(startPoint, endPoint)


def __throwBouncePoint(startPoint, endPoint):
    midPoint = startPoint + (endPoint - startPoint) / 2.0
    midPoint.setZ(0)
    return Point3(midPoint)


def doSuitAttack(attack):
    notify.debug('building suit attack in doSuitAttack: %s' % attack['name'])
    name = attack['id']
    if name == AUDIT:
        suitTrack = doAudit(attack)
    else:
        if name == BITE:
            suitTrack = doBite(attack)
        else:
            if name == BOUNCE_CHECK:
                suitTrack = doBounceCheck(attack)
            else:
                if name == BRAIN_STORM:
                    suitTrack = doBrainStorm(attack)
                else:
                    if name == BUZZ_WORD:
                        suitTrack = doBuzzWord(attack)
                    else:
                        if name == CALCULATE:
                            suitTrack = doCalculate(attack)
                        else:
                            if name == CANNED:
                                suitTrack = doCanned(attack)
                            else:
                                if name == CHOMP:
                                    suitTrack = doChomp(attack)
                                else:
                                    if name == CIGAR_SMOKE:
                                        suitTrack = doCigar(attack)
                                    else:
                                        if name == CLIPON_TIE:
                                            suitTrack = doClipOnTie(attack)
                                        else:
                                            if name == CRUNCH:
                                                suitTrack = doCrunch(attack)
                                            else:
                                                if name == DEMOTION:
                                                    suitTrack = doDemotion(attack)
                                                else:
                                                    if name == DOUBLE_TALK:
                                                        suitTrack = doDoubleTalk(attack)
                                                    else:
                                                        if name == DOWNSIZE:
                                                            suitTrack = doDownsize(attack)
                                                        else:
                                                            if name == EVICTION_NOTICE:
                                                                suitTrack = doEvictionNotice(attack)
                                                            else:
                                                                if name == EVIL_EYE:
                                                                    suitTrack = doEvilEye(attack)
                                                                else:
                                                                    if name == FILIBUSTER:
                                                                        suitTrack = doFilibuster(attack)
                                                                    else:
                                                                        if name == FILL_WITH_LEAD:
                                                                            suitTrack = doFillWithLead(attack)
                                                                        else:
                                                                            if name == FINGER_WAG:
                                                                                suitTrack = doFingerWag(attack)
                                                                            else:
                                                                                if name == FIRED:
                                                                                    suitTrack = doFired(attack)
                                                                                else:
                                                                                    if name == FIVE_O_CLOCK_SHADOW:
                                                                                        suitTrack = doDefault(attack)
                                                                                    else:
                                                                                        if name == FLOOD_THE_MARKET:
                                                                                            suitTrack = doDefault(attack)
                                                                                        else:
                                                                                            if name == FOUNTAIN_PEN:
                                                                                                suitTrack = doFountainPen(attack)
                                                                                            else:
                                                                                                if name == FREEZE_ASSETS:
                                                                                                    suitTrack = doFreezeAssets(attack)
                                                                                                else:
                                                                                                    if name == GLOWER_POWER:
                                                                                                        suitTrack = doGlowerPower(attack)
                                                                                                    else:
                                                                                                        if name == GUILT_TRIP:
                                                                                                            suitTrack = doGuiltTrip(attack)
                                                                                                        else:
                                                                                                            if name == HALF_WINDSOR:
                                                                                                                suitTrack = doHalfWindsor(attack)
                                                                                                            else:
                                                                                                                if name == HANG_UP:
                                                                                                                    suitTrack = doHangUp(attack)
                                                                                                                else:
                                                                                                                    if name == HEAD_SHRINK:
                                                                                                                        suitTrack = doHeadShrink(attack)
                                                                                                                    else:
                                                                                                                        if name == HOT_AIR:
                                                                                                                            suitTrack = doHotAir(attack)
                                                                                                                        else:
                                                                                                                            if name == JARGON:
                                                                                                                                suitTrack = doJargon(attack)
                                                                                                                            else:
                                                                                                                                if name == LEGALESE:
                                                                                                                                    suitTrack = doLegalese(attack)
                                                                                                                                else:
                                                                                                                                    if name == LIQUIDATE:
                                                                                                                                        suitTrack = doLiquidate(attack)
                                                                                                                                    else:
                                                                                                                                        if name == MARKET_CRASH:
                                                                                                                                            suitTrack = doMarketCrash(attack)
                                                                                                                                        else:
                                                                                                                                            if name == MUMBO_JUMBO:
                                                                                                                                                suitTrack = doMumboJumbo(attack)
                                                                                                                                            else:
                                                                                                                                                if name == OBJECTION:
                                                                                                                                                    suitTrack = doObjection(attack)
                                                                                                                                                else:
                                                                                                                                                    if name == PARADIGM_SHIFT:
                                                                                                                                                        suitTrack = doParadigmShift(attack)
                                                                                                                                                    else:
                                                                                                                                                        if name == PECKING_ORDER:
                                                                                                                                                            suitTrack = doPeckingOrder(attack)
                                                                                                                                                        else:
                                                                                                                                                            if name == PICK_POCKET:
                                                                                                                                                                suitTrack = doPickPocket(attack)
                                                                                                                                                            else:
                                                                                                                                                                if name == PINK_SLIP:
                                                                                                                                                                    suitTrack = doPinkSlip(attack)
                                                                                                                                                                else:
                                                                                                                                                                    if name == PLAY_HARDBALL:
                                                                                                                                                                        suitTrack = doPlayHardball(attack)
                                                                                                                                                                    else:
                                                                                                                                                                        if name == POUND_KEY:
                                                                                                                                                                            suitTrack = doPoundKey(attack)
                                                                                                                                                                        else:
                                                                                                                                                                            if name == POWER_TIE:
                                                                                                                                                                                suitTrack = doPowerTie(attack)
                                                                                                                                                                            else:
                                                                                                                                                                                if name == POWER_TRIP:
                                                                                                                                                                                    suitTrack = doPowerTrip(attack)
                                                                                                                                                                                else:
                                                                                                                                                                                    if name == QUAKE:
                                                                                                                                                                                        suitTrack = doQuake(attack)
                                                                                                                                                                                    else:
                                                                                                                                                                                        if name == RAZZLE_DAZZLE:
                                                                                                                                                                                            suitTrack = doRazzleDazzle(attack)
                                                                                                                                                                                        else:
                                                                                                                                                                                            if name == RED_TAPE:
                                                                                                                                                                                                suitTrack = doRedTape(attack)
                                                                                                                                                                                            else:
                                                                                                                                                                                                if name == RE_ORG:
                                                                                                                                                                                                    suitTrack = doReOrg(attack)
                                                                                                                                                                                                else:
                                                                                                                                                                                                    if name == RESTRAINING_ORDER:
                                                                                                                                                                                                        suitTrack = doRestrainingOrder(attack)
                                                                                                                                                                                                    else:
                                                                                                                                                                                                        if name == ROLODEX:
                                                                                                                                                                                                            suitTrack = doRolodex(attack)
                                                                                                                                                                                                        else:
                                                                                                                                                                                                            if name == RUBBER_STAMP:
                                                                                                                                                                                                                suitTrack = doRubberStamp(attack)
                                                                                                                                                                                                            else:
                                                                                                                                                                                                                if name == RUB_OUT:
                                                                                                                                                                                                                    suitTrack = doRubOut(attack)
                                                                                                                                                                                                                else:
                                                                                                                                                                                                                    if name == SACKED:
                                                                                                                                                                                                                        suitTrack = doSacked(attack)
                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                        if name == SANDTRAP:
                                                                                                                                                                                                                            suitTrack = doDefault(attack)
                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                            if name == SCHMOOZE:
                                                                                                                                                                                                                                suitTrack = doSchmooze(attack)
                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                if name == SHAKE:
                                                                                                                                                                                                                                    suitTrack = doShake(attack)
                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                    if name == SHRED:
                                                                                                                                                                                                                                        suitTrack = doShred(attack)
                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                        if name == SONG_AND_DANCE:
                                                                                                                                                                                                                                            suitTrack = doSongAndDance(attack)
                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                            if name == SPIN:
                                                                                                                                                                                                                                                suitTrack = doSpin(attack)
                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                if name == SYNERGY:
                                                                                                                                                                                                                                                    suitTrack = doSynergy(attack)
                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                    if name == TABULATE:
                                                                                                                                                                                                                                                        suitTrack = doTabulate(attack)
                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                        if name == TEE_OFF:
                                                                                                                                                                                                                                                            suitTrack = doTeeOff(attack)
                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                            if name == THROW_BOOK:
                                                                                                                                                                                                                                                                suitTrack = doDefault(attack)
                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                if name == TREMOR:
                                                                                                                                                                                                                                                                    suitTrack = doTremor(attack)
                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                    if name == WATERCOOLER:
                                                                                                                                                                                                                                                                        suitTrack = doWatercooler(attack)
                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                        if name == WITHDRAWAL:
                                                                                                                                                                                                                                                                            suitTrack = doWithdrawal(attack)
                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                            if name == WRITE_OFF:
                                                                                                                                                                                                                                                                                suitTrack = doWriteOff(attack)
                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                if name == FLEX:
                                                                                                                                                                                                                                                                                    suitTrack = doFlex(attack)
                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                    if name == PIERCE:
                                                                                                                                                                                                                                                                                        suitTrack = doPierce(attack)
                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                        if name == PUSH_SWITCH:
                                                                                                                                                                                                                                                                                            suitTrack = doPushSwitch(attack)
                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                            if name == SHADOW_TOON:
                                                                                                                                                                                                                                                                                                suitTrack = doShadowToon(attack)
                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                if name == BOSS_JUMP:
                                                                                                                                                                                                                                                                                                    suitTrack = doJumpAttack(attack)
                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                    if name == GEAR_THROW:
                                                                                                                                                                                                                                                                                                        suitTrack = doGearThrowAttack(attack)
                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                        if name == GEAR_STORM:
                                                                                                                                                                                                                                                                                                            suitTrack = doGearStormAttack(attack)
                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                            if name == CAN_ATTACK:
                                                                                                                                                                                                                                                                                                                suitTrack = doCanAttackAttack(attack)
                                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                                if name == SAFE_THROW:
                                                                                                                                                                                                                                                                                                                    suitTrack = doSafeThrowAttack(attack)
                                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                                    if name == CASH_TORNADO:
                                                                                                                                                                                                                                                                                                                        suitTrack = doCashTornadoAttack(attack)
                                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                                        if name == GAVEL:
                                                                                                                                                                                                                                                                                                                            suitTrack = doGavelAttack(attack)
                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                            if name == BOOKSHELF:
                                                                                                                                                                                                                                                                                                                                suitTrack = doBookshelfAttack(attack)
                                                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                                                if name == FORE:
                                                                                                                                                                                                                                                                                                                                    suitTrack = doForeAttack(attack)
                                                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                                                    if name == BOSS_DEMOTION:
                                                                                                                                                                                                                                                                                                                                        suitTrack = doBossDemotionAttack(attack)
                                                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                                                        if name == REORGANIZE:
                                                                                                                                                                                                                                                                                                                                            suitTrack = doReorganizeAttack(attack)
                                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                                            notify.warning('unknown attack: %d substituting Finger Wag' % name)
                                                                                                                                                                                                                                                                                                                                            suitTrack = doDefault(attack)
    camTrack = MovieCamera.chooseSuitShot(attack, suitTrack.getDuration())
    battle = attack['battle']
    target = attack['target']
    groupStatus = attack['group']
    if groupStatus == ATK_TGT_SINGLE:
        toon = target['toon']
        if toon.isDisguised:
            toonHprTrack = Sequence(Func(toon.headsUp, battle, MovieUtil.PNT3_ZERO), Func(toon.suit.loop, 'neutral'))
        else:
            toonHprTrack = Sequence(Func(toon.headsUp, battle, MovieUtil.PNT3_ZERO), Func(toon.loop, 'neutral'))
    else:
        toonHprTrack = Parallel()
        for t in target:
            toon = t['toon']
            if toon.isDisguised:
                toonHprTrack.append(Sequence(Func(toon.headsUp, battle, MovieUtil.PNT3_ZERO), Func(toon.suit.loop, 'neutral')))
            else:
                toonHprTrack.append(Sequence(Func(toon.headsUp, battle, MovieUtil.PNT3_ZERO), Func(toon.loop, 'neutral')))

        suit = attack['suit']
        neutralIval = Func(suit.loop, 'neutral')
        suitTrack = Sequence(suitTrack, neutralIval, toonHprTrack)
        suitPos = suit.getPos(battle)
        resetPos, resetHpr = battle.getActorPosHpr(suit)
        if battle.isSuitLured(suit):
            resetTrack = getResetTrack(suit, battle)
            resetSuitTrack = Sequence(resetTrack, suitTrack)
            waitTrack = Sequence(Wait(resetTrack.getDuration()), Func(battle.unlureSuit, suit))
            resetCamTrack = Sequence(waitTrack, camTrack)
            return (
             resetSuitTrack, resetCamTrack)
    return (suitTrack, camTrack)


def getResetTrack(suit, battle):
    resetPos, resetHpr = battle.getActorPosHpr(suit)
    moveDist = Vec3(suit.getPos(battle) - resetPos).length()
    moveDuration = 0.5
    walkTrack = Sequence(Func(suit.setHpr, battle, resetHpr), ActorInterval(suit, 'walk', startTime=1, duration=moveDuration, endTime=1e-05), Func(suit.loop, 'neutral'))
    moveTrack = LerpPosInterval(suit, moveDuration, resetPos, other=battle)
    return Parallel(walkTrack, moveTrack)


def __makeCancelledNodePath():
    tn = TextNode('CANCELLED')
    tn.setFont(getSuitFont())
    tn.setText(TTLocalizer.MovieSuitCancelled)
    tn.setAlign(TextNode.ACenter)
    tntop = hidden.attachNewNode('CancelledTop')
    tnpath = tntop.attachNewNode(tn)
    tnpath.setPosHpr(0, 0, 0, 0, 0, 0)
    tnpath.setScale(1)
    tnpath.setColor(0.7, 0, 0, 1)
    tnpathback = tnpath.instanceUnderNode(tntop, 'backside')
    tnpathback.setPosHpr(0, 0, 0, 180, 0, 0)
    tnpath.setScale(1)
    return tntop


def doDefault(attack):
    notify.debug('building suit attack in doDefault')
    suitName = attack['suitName']
    if suitName == 'f':
        attack['id'] = POUND_KEY
        attack['name'] = 'PoundKey'
        attack['animName'] = 'phone'
        return doPoundKey(attack)
    if suitName == 'p':
        attack['id'] = FOUNTAIN_PEN
        attack['name'] = 'FountainPen'
        attack['animName'] = 'pen-squirt'
        return doFountainPen(attack)
    if suitName == 'ym':
        attack['id'] = RUBBER_STAMP
        attack['name'] = 'RubberStamp'
        attack['animName'] = 'rubber-stamp'
        return doRubberStamp(attack)
    if suitName == 'mm':
        attack['id'] = FINGER_WAG
        attack['name'] = 'FingerWag'
        attack['animName'] = 'finger-wag'
        return doFingerWag(attack)
    if suitName == 'ds':
        attack['id'] = DEMOTION
        attack['name'] = 'Demotion'
        attack['animName'] = 'magic1'
        return doDemotion(attack)
    if suitName == 'hh':
        attack['id'] = GLOWER_POWER
        attack['name'] = 'GlowerPower'
        attack['animName'] = 'glower'
        return doGlowerPower(attack)
    if suitName == 'cr':
        attack['id'] = PICK_POCKET
        attack['name'] = 'PickPocket'
        attack['animName'] = 'pickpocket'
        return doPickPocket(attack)
    if suitName == 'tbc':
        attack['id'] = GLOWER_POWER
        attack['name'] = 'GlowerPower'
        attack['animName'] = 'glower'
        return doGlowerPower(attack)
    if suitName == 'cc':
        attack['id'] = POUND_KEY
        attack['name'] = 'PoundKey'
        attack['animName'] = 'phone'
        return doPoundKey(attack)
    if suitName == 'tm':
        attack['id'] = CLIPON_TIE
        attack['name'] = 'ClipOnTie'
        attack['animName'] = 'throw-paper'
        return doClipOnTie(attack)
    if suitName == 'nd':
        attack['id'] = PICK_POCKET
        attack['name'] = 'PickPocket'
        attack['animName'] = 'pickpocket'
        return doPickPocket(attack)
    if suitName == 'gh':
        attack['id'] = FOUNTAIN_PEN
        attack['name'] = 'FountainPen'
        attack['animName'] = 'pen-squirt'
        return doFountainPen(attack)
    if suitName == 'ms':
        attack['id'] = BRAIN_STORM
        attack['name'] = 'BrainStorm'
        attack['animName'] = 'effort'
        return doBrainStorm(attack)
    if suitName == 'tf':
        attack['id'] = RED_TAPE
        attack['name'] = 'RedTape'
        attack['animName'] = 'throw-object'
        return doRedTape(attack)
    if suitName == 'm':
        attack['id'] = BUZZ_WORD
        attack['name'] = 'BuzzWord'
        attack['animName'] = 'speak'
        return doBuzzWord(attack)
    if suitName == 'mh':
        attack['id'] = RAZZLE_DAZZLE
        attack['name'] = 'RazzleDazzle'
        attack['animName'] = 'smile'
        return doRazzleDazzle(attack)
    if suitName == 'sc':
        attack['id'] = WATERCOOLER
        attack['name'] = 'Watercooler'
        attack['animName'] = 'water-cooler'
        return doWatercooler(attack)
    if suitName == 'pp':
        attack['id'] = BOUNCE_CHECK
        attack['name'] = 'BounceCheck'
        attack['animName'] = 'throw-paper'
        return doBounceCheck(attack)
    if suitName == 'tw':
        attack['id'] = GLOWER_POWER
        attack['name'] = 'GlowerPower'
        attack['animName'] = 'glower'
        return doGlowerPower(attack)
    if suitName == 'bc':
        attack['id'] = AUDIT
        attack['name'] = 'Audit'
        attack['animName'] = 'phone'
        return doAudit(attack)
    if suitName == 'nc':
        attack['id'] = RED_TAPE
        attack['name'] = 'RedTape'
        attack['animName'] = 'throw-object'
        return doRedTape(attack)
    if suitName == 'mb':
        attack['id'] = LIQUIDATE
        attack['name'] = 'Liquidate'
        attack['animName'] = 'magic1'
        return doLiquidate(attack)
    if suitName == 'ls':
        attack['id'] = WRITE_OFF
        attack['name'] = 'WriteOff'
        attack['animName'] = 'hold-pencil'
        return doWriteOff(attack)
    if suitName == 'rb':
        attack['id'] = TEE_OFF
        attack['name'] = 'TeeOff'
        attack['animName'] = 'golf-club-swing'
        return doTeeOff(attack)
    if suitName == 'bf':
        attack['id'] = RUBBER_STAMP
        attack['name'] = 'RubberStamp'
        attack['animName'] = 'rubber-stamp'
        return doRubberStamp(attack)
    if suitName == 'b':
        attack['id'] = EVICTION_NOTICE
        attack['name'] = 'EvictionNotice'
        attack['animName'] = 'throw-paper'
        return doEvictionNotice(attack)
    if suitName == 'dt':
        attack['id'] = RUBBER_STAMP
        attack['name'] = 'RubberStamp'
        attack['animName'] = 'rubber-stamp'
        return doRubberStamp(attack)
    if suitName == 'ac':
        attack['id'] = RED_TAPE
        attack['name'] = 'RedTape'
        attack['animName'] = 'throw-object'
        return doRedTape(attack)
    if suitName == 'bs':
        attack['id'] = FINGER_WAG
        attack['name'] = 'FingerWag'
        attack['animName'] = 'finger-wag'
        return doFingerWag(attack)
    if suitName == 'sd':
        attack['id'] = WRITE_OFF
        attack['name'] = 'WriteOff'
        attack['animName'] = 'hold-pencil'
        return doWriteOff(attack)
    if suitName == 'le':
        attack['id'] = JARGON
        attack['name'] = 'Jargon'
        attack['animName'] = 'speak'
        return doJargon(attack)
    if suitName == 'bw':
        attack['id'] = FINGER_WAG
        attack['name'] = 'FingerWag'
        attack['animName'] = 'finger-wag'
        return doFingerWag(attack)
    if suitName == 'bfs':
        attack['id'] = FLEX
        attack['name'] = 'Flex'
        attack['animName'] = 'glower'
        return doFlex(attack)
    if suitName == 'pb':
        attack['id'] = FINGER_WAG
        attack['name'] = 'FingerWag'
        attack['animName'] = 'finger-wag'
        return doFingerWag(attack)
    if suitName == 'sm':
        attack['id'] = TEE_OFF
        attack['name'] = 'TeeOff'
        attack['animName'] = 'golf-club-swing'
        return doTeeOff(attack)
    if suitName == 'cag':
        attack['id'] = PUSH_SWITCH
        attack['name'] = 'PushSwitch'
        attack['animName'] = 'phone'
        return doPushSwitch(attack)
    self.notify.error('doDefault() - unsupported suit type: %s' % suitName)
    return


def getSuitTrack(attack, delay=1e-06, splicedAnims=None):
    suit = attack['suit']
    battle = attack['battle']
    tauntIndex = attack['taunt']
    target = attack['target']
    toon = target['toon']
    targetPos = toon.getPos(battle)
    taunt = getAttackTaunt(attack['name'], tauntIndex)
    trapStorage = {}
    trapStorage['trap'] = None
    track = Sequence(Wait(delay), Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout))

    def reparentTrap(suit=suit, battle=battle, trapStorage=trapStorage):
        trapProp = suit.battleTrapProp
        if trapProp != None:
            trapProp.wrtReparentTo(battle)
            trapStorage['trap'] = trapProp
        return

    track.append(Func(reparentTrap))
    track.append(Func(suit.headsUp, battle, targetPos))
    if splicedAnims:
        track.append(getSplicedAnimsTrack(splicedAnims, actor=suit))
    else:
        track.append(ActorInterval(suit, attack['animName']))
    origPos, origHpr = battle.getActorPosHpr(suit)
    track.append(Func(suit.setHpr, battle, origHpr))

    def returnTrapToSuit(suit=suit, trapStorage=trapStorage):
        trapProp = trapStorage['trap']
        if trapProp != None:
            if trapProp.getName() == 'traintrack':
                notify.debug('deliberately not parenting traintrack to suit')
            else:
                trapProp.wrtReparentTo(suit)
            suit.battleTrapProp = trapProp
        return

    track.append(Func(returnTrapToSuit))
    track.append(Func(suit.clearChat))
    return track


def getSuitAnimTrack(attack, delay=0):
    suit = attack['suit']
    tauntIndex = attack['taunt']
    taunt = getAttackTaunt(attack['name'], tauntIndex)
    return Sequence(Wait(delay), Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), ActorInterval(attack['suit'], attack['animName']), Func(suit.clearChat))


def getPartTrack(particleEffect, startDelay, durationDelay, partExtraArgs):
    particleEffect = partExtraArgs[0]
    parent = partExtraArgs[1]
    if len(partExtraArgs) > 2:
        worldRelative = partExtraArgs[2]
    else:
        worldRelative = 1
    return Sequence(Wait(startDelay), ParticleInterval(particleEffect, parent, worldRelative, duration=durationDelay, cleanup=True))


def getToonTrack(attack, damageDelay=1e-06, damageAnimNames=None, dodgeDelay=0.0001, dodgeAnimNames=None, splicedDamageAnims=None, splicedDodgeAnims=None, target=None, showDamageExtraTime=0.01, showMissedExtraTime=0.5, flexOnEx=0, prop=None, splitTripleDmg=False, hideDmg=False):
    if not target:
        target = attack['target']
    toon = target['toon']
    battle = attack['battle']
    suit = attack['suit']
    suitPos = suit.getPos(battle)
    if splitTripleDmg:
        if target['hp'] == 1:
            dmg = 1
        else:
            dmg = int(target['hp'] / 3)
    else:
        dmg = target['hp']
    animTrack = Sequence()
    animTrack.append(Func(toon.headsUp, battle, suitPos))
    if dmg > 0:
        if flexOnEx == 1:
            animTrack.append(getToonTakeDamageTrack(toon, target['died'], dmg, damageDelay, damageAnimNames, splicedDamageAnims, showDamageExtraTime, battle, prop))
        else:
            animTrack.append(getToonTakeDamageTrack(toon, target['died'], dmg, damageDelay, damageAnimNames, splicedDamageAnims, showDamageExtraTime, hideDmg=hideDmg))
        return animTrack
    animTrack.append(getToonDodgeTrack(target, dodgeDelay, dodgeAnimNames, splicedDodgeAnims, showMissedExtraTime))
    indicatorTrack = Sequence(Wait(dodgeDelay + showMissedExtraTime), Func(MovieUtil.indicateMissed, toon))
    return Parallel(animTrack, indicatorTrack)


def getToonTracks(attack, damageDelay=1e-06, damageAnimNames=None, dodgeDelay=1e-06, dodgeAnimNames=None, splicedDamageAnims=None, splicedDodgeAnims=None, showDamageExtraTime=0.01, showMissedExtraTime=0.5, splitTripleDmg=False, hideDmg=False):
    toonTracks = Parallel()
    targets = attack['target']
    for i in range(len(targets)):
        tgt = targets[i]
        toonTracks.append(getToonTrack(attack, damageDelay, damageAnimNames, dodgeDelay, dodgeAnimNames, splicedDamageAnims, splicedDodgeAnims, target=tgt, showDamageExtraTime=showDamageExtraTime, showMissedExtraTime=showMissedExtraTime, splitTripleDmg=splitTripleDmg, hideDmg=hideDmg))

    return toonTracks


def getToonDodgeTrack(target, dodgeDelay, dodgeAnimNames, splicedDodgeAnims, showMissedExtraTime):
    toon = target['toon']
    toonTrack = Sequence()
    toonTrack.append(Wait(dodgeDelay))
    if dodgeAnimNames:
        for d in dodgeAnimNames:
            if d == 'sidestep':
                toonTrack.append(getAllyToonsDodgeParallel(target))
            elif d == 'jump' and toon.isDisguised:
                if toon.suit.style.body == 'a':
                    toonTrack.append(ActorInterval(toon.suit, 'slip-forward', startFrame=55))
                elif toon.suit.style.body == 'b':
                    toonTrack.append(Sequence(ActorInterval(toon.suit, 'quick-jump', playRate=5, endFrame=15), ActorInterval(toon.suit, 'quick-jump', startFrame=15, endFrame=30), ActorInterval(toon.suit, 'quick-jump', startFrame=107)))
                elif toon.suit.style.body == 'c':
                    toonTrack.append(ActorInterval(toon.suit, 'slip-forward', startFrame=59))
            else:
                toonTrack.append(ActorInterval(toon, d))

    else:
        toonTrack.append(getSplicedAnimsTrack(splicedDodgeAnims, actor=toon))
    if toon.isDisguised:
        toonTrack.append(Func(toon.suit.loop, 'neutral'))
    else:
        toonTrack.append(Func(toon.loop, 'neutral'))
    return toonTrack


def getAllyToonsDodgeParallel(target):
    toon = target['toon']
    leftToons = target['leftToons']
    rightToons = target['rightToons']
    if len(leftToons) > len(rightToons):
        PoLR = rightToons
        PoMR = leftToons
    else:
        PoLR = leftToons
        PoMR = rightToons
    upper = 1 + 4 * abs(len(leftToons) - len(rightToons))
    if random.randint(0, upper) > 0:
        toonDodgeList = PoLR
    else:
        toonDodgeList = PoMR
    if toonDodgeList is leftToons:
        sidestepAnim = 'sidestep-left'
        soundEffect = globalBattleSoundCache.getSound('AV_side_step.ogg')
    else:
        sidestepAnim = 'sidestep-right'
        soundEffect = globalBattleSoundCache.getSound('AV_jump_to_side.ogg')
    toonTracks = Parallel()
    for t in toonDodgeList:
        if t.isDisguised:
            toonTracks.append(Sequence(ActorInterval(t.suit, sidestepAnim), Func(t.suit.loop, 'neutral')))
        else:
            toonTracks.append(Sequence(ActorInterval(t, sidestepAnim), Func(t.loop, 'neutral')))

    if toon.isDisguised:
        toonTracks.append(Sequence(ActorInterval(toon.suit, sidestepAnim), Func(toon.suit.loop, 'neutral')))
    else:
        toonTracks.append(Sequence(ActorInterval(toon, sidestepAnim), Func(toon.loop, 'neutral')))
    toonTracks.append(Sequence(Wait(0.5), SoundInterval(soundEffect, node=toon)))
    return toonTracks


def getPropTrack(prop, parent, posPoints, appearDelay, remainDelay, scaleUpPoint=Point3(1), scaleUpTime=0.5, scaleDownTime=0.5, startScale=Point3(0.01), anim=0, propName='none', animDuration=0.0, animStartTime=0.0):
    if anim == 1:
        track = Sequence(Wait(appearDelay), Func(__showProp, prop, parent, *posPoints), LerpScaleInterval(prop, scaleUpTime, scaleUpPoint, startScale=startScale), ActorInterval(prop, propName, duration=animDuration, startTime=animStartTime), Wait(remainDelay), Func(MovieUtil.removeProp, prop))
    else:
        track = Sequence(Wait(appearDelay), Func(__showProp, prop, parent, *posPoints), LerpScaleInterval(prop, scaleUpTime, scaleUpPoint, startScale=startScale), Wait(remainDelay), LerpScaleInterval(prop, scaleDownTime, MovieUtil.PNT3_NEARZERO), Func(MovieUtil.removeProp, prop))
    return track


def getPropAppearTrack(prop, parent, posPoints, appearDelay, scaleUpPoint=Point3(1), scaleUpTime=0.5, startScale=Point3(0.01), poseExtraArgs=None):
    propTrack = Sequence(Wait(appearDelay), Func(__showProp, prop, parent, *posPoints))
    if poseExtraArgs:
        propTrack.append(Func(prop.pose, *poseExtraArgs))
    propTrack.append(LerpScaleInterval(prop, scaleUpTime, scaleUpPoint, startScale=startScale))
    return propTrack


def getPropThrowTrack(attack, prop, hitPoints=[], missPoints=[], hitDuration=0.5, missDuration=0.5, hitPointNames='none', missPointNames='none', lookAt='none', groundPointOffSet=0, missScaleDown=None, parent=render):
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    battle = attack['battle']

    def getLambdas(list, prop, toon):
        for i in range(len(list)):
            if list[i] == 'face':
                list[i] = lambda toon=toon: __toonFacePoint(toon)
            elif list[i] == 'miss':
                list[i] = lambda prop=prop, toon=toon: __toonMissPoint(prop, toon)
            elif list[i] == 'bounceHit':
                list[i] = lambda prop=prop, toon=toon: __throwBounceHitPoint(prop, toon)
            elif list[i] == 'bounceMiss':
                list[i] = lambda prop=prop, toon=toon: __throwBounceMissPoint(prop, toon)

        return list

    if hitPointNames != 'none':
        hitPoints = getLambdas(hitPointNames, prop, toon)
    if missPointNames != 'none':
        missPoints = getLambdas(missPointNames, prop, toon)
    propTrack = Sequence()
    propTrack.append(Func(battle.movie.needRestoreRenderProp, prop))
    propTrack.append(Func(prop.wrtReparentTo, parent))
    if lookAt != 'none':
        propTrack.append(Func(prop.lookAt, lookAt))
    if dmg > 0:
        for i in range(len(hitPoints)):
            pos = hitPoints[i]
            propTrack.append(LerpPosInterval(prop, hitDuration, pos=pos))

    else:
        for i in range(len(missPoints)):
            pos = missPoints[i]
            propTrack.append(LerpPosInterval(prop, missDuration, pos=pos))

    if missScaleDown:
        propTrack.append(LerpScaleInterval(prop, missScaleDown, MovieUtil.PNT3_NEARZERO))
    propTrack.append(Func(MovieUtil.removeProp, prop))
    propTrack.append(Func(battle.movie.clearRenderProp, prop))
    return propTrack


def getThrowTrack(object, target, duration=1.0, parent=render, gravity=-32.144):
    values = {}

    def calcOriginAndVelocity(object=object, target=target, values=values, duration=duration, parent=parent, gravity=gravity):
        if callable(target):
            target = target()
        object.wrtReparentTo(parent)
        values['origin'] = object.getPos(parent)
        origin = object.getPos(parent)
        values['velocity'] = (target[2] - origin[2] - 0.5 * gravity * duration * duration) / duration

    return Sequence(Func(calcOriginAndVelocity), LerpFunctionInterval(throwPos, fromData=0.0, toData=1.0, duration=duration, extraArgs=[object,
     duration,
     target,
     values,
     gravity]))


def throwPos(t, object, duration, target, values, gravity=-32.144):
    origin = values['origin']
    velocity = values['velocity']
    if callable(target):
        target = target()
    x = origin[0] * (1 - t) + target[0] * t
    y = origin[1] * (1 - t) + target[1] * t
    time = t * duration
    z = origin[2] + velocity * time + 0.5 * gravity * time * time
    object.setPos(x, y, z)


def getToonTakeDamageTrack(toon, died, dmg, delay, damageAnimNames=None, splicedDamageAnims=None, showDamageExtraTime=0.01, battle=None, prop=None, hideDmg=False):
    toonTrack = Sequence()
    toonTrack.append(Wait(delay))
    if damageAnimNames:
        for d in damageAnimNames:
            if toon.isDisguised:
                if d == 'conked':
                    toonTrack.append(ActorInterval(toon.suit, 'squirt-small-react'))
                elif d.startswith('slip'):
                    toonTrack.append(ActorInterval(toon.suit, d))
                elif d == 'jump':
                    if toon.suit.style.body == 'a':
                        toonTrack.append(ActorInterval(toon.suit, 'slip-forward', startFrame=55))
                    elif toon.suit.style.body == 'b':
                        toonTrack.append(Sequence(ActorInterval(toon.suit, 'quick-jump', playRate=5, endFrame=15), ActorInterval(toon.suit, 'quick-jump', startFrame=15, endFrame=30), ActorInterval(toon.suit, 'quick-jump', startFrame=107)))
                    elif toon.suit.style.body == 'c':
                        toonTrack.append(ActorInterval(toon.suit, 'slip-forward', startFrame=59))
                elif d == 'suitQuicksandAnim':
                    print battle
                    sinkPos1 = toon.getPos()
                    sinkPos2 = toon.getPos()
                    dropPos = toon.getPos()
                    landPos = toon.getPos()
                    sinkPos1.setZ(sinkPos1.getZ() - 3.1)
                    sinkPos2.setZ(sinkPos2.getZ() - 9.1)
                    dropPos.setZ(dropPos.getZ() + 15)
                    moveTrack = Sequence(Wait(0.9), LerpPosInterval(toon, 0.9, sinkPos1), LerpPosInterval(toon, 0.4, sinkPos2), Func(toon.setPos, dropPos), Func(toon.wrtReparentTo, hidden), Wait(1.1), Func(toon.wrtReparentTo, render), LerpPosInterval(toon, 0.3, landPos))
                    animTrack = Sequence(ActorInterval(toon.suit, 'flail'), ActorInterval(toon.suit, 'flail', startTime=1.1), Wait(0.7), ActorInterval(toon.suit, 'slip-forward', duration=2.1))
                    toonTrack.append(Parallel(moveTrack, animTrack))
                else:
                    toonTrack.append(ActorInterval(toon.suit, 'pie-small-react'))
            else:
                toonTrack.append(ActorInterval(toon, d))

        if hideDmg:
            indicatorTrack = Sequence(Wait(delay + showDamageExtraTime))
        else:
            indicatorTrack = Sequence(Wait(delay + showDamageExtraTime), Func(__doDamage, toon, dmg, died))
    else:
        if toon.isDisguised:
            splicedAnims = getSplicedAnimsTrack(splicedDamageAnims, flexex=1, actor=toon.suit)
        else:
            splicedAnims = getSplicedAnimsTrack(splicedDamageAnims, actor=toon)
        toonTrack.append(splicedAnims)
        if hideDmg:
            indicatorTrack = Sequence(Wait(delay + showDamageExtraTime))
        else:
            indicatorTrack = Sequence(Wait(delay + showDamageExtraTime), Func(__doDamage, toon, dmg, died))
    toonTrack.append(Func(toon.loop, 'neutral'))
    if died:
        toonTrack.append(Wait(5.0))
    return Parallel(toonTrack, indicatorTrack)


def getSplicedAnimsTrack(anims, flexex=0, actor=None):
    track = Sequence()
    for nextAnim in anims:
        delay = 1e-06
        if flexex == 1:
            if nextAnim[0] == 'conked':
                nextAnim[0] = 'squirt-small-react'
            elif nextAnim[0].startswith('slip'):
                pass
            elif nextAnim[0] == 'melt':
                nextAnim[0] = 'flail'
            else:
                nextAnim[0] = 'pie-small-react'
        if len(nextAnim) >= 2:
            if nextAnim[1] > 0:
                delay = nextAnim[1]
        if len(nextAnim) <= 0:
            track.append(Wait(delay))
        elif len(nextAnim) == 1:
            track.append(ActorInterval(actor, nextAnim[0]))
        elif len(nextAnim) == 2:
            track.append(Wait(delay))
            track.append(ActorInterval(actor, nextAnim[0]))
        elif len(nextAnim) == 3:
            track.append(Wait(delay))
            track.append(ActorInterval(actor, nextAnim[0], startTime=nextAnim[2]))
        elif len(nextAnim) == 4:
            track.append(Wait(delay))
            duration = nextAnim[3]
            if duration < 0:
                startTime = nextAnim[2]
                endTime = startTime + duration
                if endTime <= 0:
                    endTime = 0.01
                track.append(ActorInterval(actor, nextAnim[0], startTime=startTime, endTime=endTime))
            else:
                track.append(ActorInterval(actor, nextAnim[0], startTime=nextAnim[2], duration=duration))
        elif len(nextAnim) == 5:
            track.append(Wait(delay))
            track.append(ActorInterval(nextAnim[4], nextAnim[0], startTime=nextAnim[2], duration=nextAnim[3]))

    return track


def getSplicedLerpAnims(animName, origDuration, newDuration, startTime=0, fps=30, reverse=0):
    anims = []
    addition = 0
    numAnims = origDuration * fps
    timeInterval = newDuration / numAnims
    animInterval = origDuration / numAnims
    if reverse == 1:
        animInterval = -animInterval
    for i in range(0, int(numAnims)):
        anims.append([animName,
         timeInterval,
         startTime + addition,
         animInterval])
        addition += animInterval

    return anims


def getSoundTrack(fileName, delay=0.01, startTime=0.0, duration=None, node=None):
    soundEffect = globalBattleSoundCache.getSound(fileName)
    if duration:
        return Sequence(Wait(delay), SoundInterval(soundEffect, startTime=startTime, duration=duration, node=node))
    return Sequence(Wait(delay), SoundInterval(soundEffect, startTime=startTime, node=node))


def doClipOnTie(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    tie = globalPropPool.getProp('clip-on-tie')
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        throwDelay = 2.17
        damageDelay = 3.3
        dodgeDelay = 3.1
    else:
        if suitType == 'b':
            throwDelay = 2.17
            damageDelay = 3.3
            dodgeDelay = 3.1
        else:
            if suitType == 'c':
                throwDelay = 1.45
                damageDelay = 2.61
                dodgeDelay = 2.34
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(0.66, 0.51, 0.28), VBase3(-69.652, -17.199, 67.96)]
    tiePropTrack = Sequence(getPropAppearTrack(tie, suit.getRightHand(), posPoints, 0.5, MovieUtil.PNT3_ONE, scaleUpTime=0.5, poseExtraArgs=['clip-on-tie', 0]))
    if dmg > 0:
        tiePropTrack.append(ActorInterval(tie, 'clip-on-tie', duration=throwDelay, startTime=1.1))
    else:
        tiePropTrack.append(Wait(throwDelay))
    tiePropTrack.append(Func(tie.setHpr, Point3(0, -90, 0)))
    tiePropTrack.append(getPropThrowTrack(attack, tie, [__toonFacePoint(toon)], [__toonGroundPoint(attack, toon, 0.1)], hitDuration=0.4, missDuration=0.8, missScaleDown=1.2))
    toonTrack = getToonTrack(attack, damageDelay, ['conked'], dodgeDelay, ['sidestep'])
    throwSound = getSoundTrack('SA_powertie_throw.ogg', delay=throwDelay + 1, node=suit)
    return Parallel(suitTrack, toonTrack, tiePropTrack, throwSound)


def doPoundKey(attack):
    suit = attack['suit']
    battle = attack['battle']
    phone = globalPropPool.getProp('phone')
    receiver = globalPropPool.getProp('receiver')
    BattleParticles.loadParticles()
    particleEffect = BattleParticles.createParticleEffect('PoundKey')
    BattleParticles.setEffectTexture(particleEffect, 'poundsign', color=Vec4(0, 0, 0, 1))
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(particleEffect, 2.1, 1.55, [particleEffect, suit, 0])
    phonePosPoints = [Point3(0.23, 0.17, -0.11), VBase3(5.939, 2.763, -177.591)]
    receiverPosPoints = [Point3(0.23, 0.17, -0.11), VBase3(5.939, 2.763, -177.591)]
    propTrack = Sequence(Wait(0.3), Func(__showProp, phone, suit.getLeftHand(), phonePosPoints[0], phonePosPoints[1]), Func(__showProp, receiver, suit.getLeftHand(), receiverPosPoints[0], receiverPosPoints[1]), LerpScaleInterval(phone, 0.5, MovieUtil.PNT3_ONE, MovieUtil.PNT3_NEARZERO), Wait(0.74), Func(receiver.wrtReparentTo, suit.getRightHand()), LerpPosHprInterval(receiver, 0.0001, Point3(-0.45, 0.48, -0.62), VBase3(-87.47, -18.21, 7.82)), Wait(3.14), Func(receiver.wrtReparentTo, phone), Wait(0.62), LerpScaleInterval(phone, 0.5, MovieUtil.PNT3_NEARZERO), Func(MovieUtil.removeProps, [receiver, phone]))
    toonTrack = getToonTrack(attack, 2.7, ['cringe'], 1.9, ['sidestep'])
    soundTrack = getSoundTrack('SA_hangup.ogg', delay=1.3, node=suit)
    return Parallel(suitTrack, toonTrack, propTrack, partTrack, soundTrack)


def doShred(attack):
    suit = attack['suit']
    battle = attack['battle']
    paper = globalPropPool.getProp('shredder-paper')
    shredder = globalPropPool.getProp('shredder')
    particleEffect = BattleParticles.createParticleEffect('Shred')
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(particleEffect, 3.5, 1.9, [particleEffect, suit, 0])
    paperPosPoints = [Point3(0.59, -0.31, 0.81), VBase3(79.224, 32.576, -179.449)]
    paperPropTrack = getPropTrack(paper, suit.getRightHand(), paperPosPoints, 2.4, 1e-05, scaleUpTime=0.2, anim=1, propName='shredder-paper', animDuration=1.5, animStartTime=2.8)
    shredderPosPoints = [Point3(0, -0.12, -0.34), VBase3(-90.0, -53.77, -0.0)]
    shredderPropTrack = getPropTrack(shredder, suit.getLeftHand(), shredderPosPoints, 1, 3, scaleUpPoint=Point3(4.81, 4.81, 4.81))
    toonTrack = getToonTrack(attack, suitTrack.getDuration() - 1.1, ['conked'], suitTrack.getDuration() - 3.1, ['sidestep'])
    soundTrack = getSoundTrack('SA_shred.ogg', delay=3.4, node=suit)
    return Parallel(suitTrack, paperPropTrack, shredderPropTrack, partTrack, toonTrack, soundTrack)


def doFillWithLead(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    pencil = globalPropPool.getProp('pencil')
    sharpener = globalPropPool.getProp('sharpener')
    BattleParticles.loadParticles()
    sprayEffect = BattleParticles.createParticleEffect(file='fillWithLeadSpray')
    headSmotherEffect = BattleParticles.createParticleEffect(file='fillWithLeadSmother')
    torsoSmotherEffect = BattleParticles.createParticleEffect(file='fillWithLeadSmother')
    legsSmotherEffect = BattleParticles.createParticleEffect(file='fillWithLeadSmother')
    BattleParticles.setEffectTexture(sprayEffect, 'roll-o-dex', color=Vec4(0, 0, 0, 1))
    BattleParticles.setEffectTexture(headSmotherEffect, 'roll-o-dex', color=Vec4(0, 0, 0, 1))
    BattleParticles.setEffectTexture(torsoSmotherEffect, 'roll-o-dex', color=Vec4(0, 0, 0, 1))
    BattleParticles.setEffectTexture(legsSmotherEffect, 'roll-o-dex', color=Vec4(0, 0, 0, 1))
    suitTrack = getSuitTrack(attack)
    sprayTrack = getPartTrack(sprayEffect, 2.5, 1.9, [sprayEffect, suit, 0])
    pencilPosPoints = [Point3(-0.29, -0.33, -0.13), VBase3(160.565, -11.653, -169.244)]
    pencilPropTrack = getPropTrack(pencil, suit.getRightHand(), pencilPosPoints, 0.7, 3.2, scaleUpTime=0.2)
    sharpenerPosPoints = [Point3(0.0, 0.0, -0.03), MovieUtil.PNT3_ZERO]
    sharpenerPropTrack = getPropTrack(sharpener, suit.getLeftHand(), sharpenerPosPoints, 1.3, 2.3, scaleUpPoint=MovieUtil.PNT3_ONE)
    damageAnims = []
    damageAnims.append(['conked',
     suitTrack.getDuration() - 1.5,
     1e-05,
     1.4])
    damageAnims.append(['conked',
     1e-05,
     0.7,
     0.7])
    damageAnims.append(['conked',
     1e-05,
     0.7,
     0.7])
    damageAnims.append(['conked', 1e-05, 1.4])
    toonTrack = getToonTrack(attack, splicedDamageAnims=damageAnims, dodgeDelay=suitTrack.getDuration() - 3.1, dodgeAnimNames=['sidestep'], showDamageExtraTime=4.5, showMissedExtraTime=1.6)
    animal = toon.style.getAnimal()
    bodyScale = ToontownGlobals.toonBodyScales[animal]
    headEffectHeight = __toonFacePoint(toon).getZ()
    legsHeight = ToontownGlobals.legHeightDict[toon.style.legs] * bodyScale
    torsoEffectHeight = ToontownGlobals.torsoHeightDict[toon.style.torso] * bodyScale / 2 + legsHeight
    legsEffectHeight = legsHeight / 2
    effectX = headSmotherEffect.getX()
    effectY = headSmotherEffect.getY()
    headSmotherEffect.setPos(effectX, effectY - 1.5, headEffectHeight)
    torsoSmotherEffect.setPos(effectX, effectY - 1, torsoEffectHeight)
    legsSmotherEffect.setPos(effectX, effectY - 0.6, legsEffectHeight)
    partDelay = 3.5
    partIvalDelay = 0.7
    partDuration = 1.0
    headTrack = getPartTrack(headSmotherEffect, partDelay, partDuration, [headSmotherEffect, toon, 0])
    torsoTrack = getPartTrack(torsoSmotherEffect, partDelay + partIvalDelay, partDuration, [torsoSmotherEffect, toon, 0])
    legsTrack = getPartTrack(legsSmotherEffect, partDelay + partIvalDelay * 2, partDuration, [legsSmotherEffect, toon, 0])

    def colorParts(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(LerpColorScaleInterval(nextPart, 0.2, Point4(0, 0, 0, 1)))

        return track

    def resetParts(parts):
        track = Sequence()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(LerpColorScaleInterval(nextPart, 0.2, Point4(1, 1, 1, 1)))
            track.append(Func(nextPart.clearColorScale))

        return track

    if dmg > 0:
        colorTrack = Sequence()
        headParts = toon.getHeadParts()
        torsoParts = toon.getTorsoParts()
        legsParts = toon.getLegsParts()
        colorTrack.append(Wait(partDelay + 0.2))
        colorTrack.append(Func(battle.movie.needRestoreColor))
        colorTrack.append(colorParts(headParts))
        colorTrack.append(Wait(partIvalDelay))
        colorTrack.append(colorParts(torsoParts))
        colorTrack.append(Wait(partIvalDelay))
        colorTrack.append(colorParts(legsParts))
        colorTrack.append(Wait(0.9))
        colorTrack.append(resetParts(headParts))
        colorTrack.append(resetParts(torsoParts))
        colorTrack.append(resetParts(legsParts))
        colorTrack.append(Wait(partIvalDelay))
        colorTrack.append(Func(battle.movie.clearRestoreColor))
        return Parallel(suitTrack, pencilPropTrack, sharpenerPropTrack, sprayTrack, headTrack, torsoTrack, legsTrack, colorTrack, toonTrack)
    return Parallel(suitTrack, pencilPropTrack, sharpenerPropTrack, sprayTrack, toonTrack)


def doFountainPen(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    pen = globalPropPool.getProp('pen')

    def getPenTip(pen=pen):
        tip = pen.find('**/joint_toSpray')
        return tip.getPos(render)

    hitPoint = lambda toon=toon: __toonFacePoint(toon)
    missPoint = lambda prop=pen, toon=toon: __toonMissPoint(prop, toon, 0, parent=render)
    hitSprayTrack = MovieUtil.getSprayTrack(battle, VBase4(0, 0, 0, 1), getPenTip, hitPoint, 0.2, 0.2, 0.2, horizScale=0.1, vertScale=0.1)
    missSprayTrack = MovieUtil.getSprayTrack(battle, VBase4(0, 0, 0, 1), getPenTip, missPoint, 0.2, 0.2, 0.2, horizScale=0.1, vertScale=0.1)
    suitTrack = getSuitTrack(attack)
    propTrack = Sequence(Wait(0.01), Func(__showProp, pen, suit.getRightHand(), MovieUtil.PNT3_ZERO), LerpScaleInterval(pen, 0.5, Point3(1.5, 1.5, 1.5)), Wait(1.05))
    if dmg > 0:
        propTrack.append(hitSprayTrack)
    else:
        propTrack.append(missSprayTrack)
    propTrack += [LerpScaleInterval(pen, 0.5, MovieUtil.PNT3_NEARZERO), Func(MovieUtil.removeProp, pen)]
    splashTrack = Sequence()
    if dmg > 0:

        def prepSplash(splash, targetPoint):
            splash.reparentTo(render)
            splash.setPos(targetPoint)
            scale = splash.getScale()
            splash.setBillboardPointWorld()
            splash.setScale(scale)

        splash = globalPropPool.getProp('splash-from-splat')
        splash.setColor(0, 0, 0, 1)
        splash.setScale(0.15)
        splashTrack = Sequence(Func(battle.movie.needRestoreRenderProp, splash), Wait(1.65), Func(prepSplash, splash, __toonFacePoint(toon)), ActorInterval(splash, 'splash-from-splat'), Func(MovieUtil.removeProp, splash), Func(battle.movie.clearRenderProp, splash))
        headParts = toon.getHeadParts()
        splashTrack.append(Func(battle.movie.needRestoreColor))
        for partNum in range(0, headParts.getNumPaths()):
            nextPart = headParts.getPath(partNum)
            splashTrack.append(Func(nextPart.setColorScale, Vec4(0, 0, 0, 1)))

        splashTrack.append(Func(MovieUtil.removeProp, splash))
        splashTrack.append(Wait(2.1))
        for partNum in range(0, headParts.getNumPaths()):
            nextPart = headParts.getPath(partNum)
            splashTrack.append(LerpColorScaleInterval(nextPart, 0.1, Point4(1, 1, 1, 1)))
            splashTrack.append(Func(nextPart.clearColorScale))

        splashTrack.append(Func(battle.movie.clearRestoreColor))
    penSpill = BattleParticles.createParticleEffect(file='penSpill')
    penSpill.setPos(getPenTip())
    penSpillTrack = getPartTrack(penSpill, 1.4, 0.7, [penSpill, pen, 0])
    toonTrack = getToonTrack(attack, 1.81, ['conked'], dodgeDelay=0.11, splicedDodgeAnims=[['duck', 0.01, 0.6]], showMissedExtraTime=1.66)
    soundTrack = getSoundTrack('SA_fountain_pen.ogg', delay=1.6, node=suit)
    return Parallel(suitTrack, toonTrack, propTrack, soundTrack, penSpillTrack, splashTrack)


def doRubOut(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    pad = globalPropPool.getProp('pad')
    pencil = globalPropPool.getProp('pencil')
    headEffect = BattleParticles.createParticleEffect('RubOut', color=toon.style.getHeadColor())
    torsoEffect = BattleParticles.createParticleEffect('RubOut', color=toon.style.getArmColor())
    legsEffect = BattleParticles.createParticleEffect('RubOut', color=toon.style.getLegColor())
    suitTrack = getSuitTrack(attack)
    padPosPoints = [Point3(-0.66, 0.81, -0.06), VBase3(14.93, -2.29, 180.0)]
    padPropTrack = getPropTrack(pad, suit.getLeftHand(), padPosPoints, 0.5, 2.57)
    pencilPosPoints = [Point3(0.04, -0.38, -0.1), VBase3(-170.223, -3.762, -62.929)]
    pencilPropTrack = getPropTrack(pencil, suit.getRightHand(), pencilPosPoints, 0.5, 2.57)
    toonTrack = getToonTrack(attack, 2.2, ['conked'], 2.0, ['jump'])
    hideTrack = Sequence()
    headParts = toon.getHeadParts()
    torsoParts = toon.getTorsoParts()
    legsParts = toon.getLegsParts()
    animal = toon.style.getAnimal()
    bodyScale = ToontownGlobals.toonBodyScales[animal]
    headEffectHeight = __toonFacePoint(toon).getZ()
    legsHeight = ToontownGlobals.legHeightDict[toon.style.legs] * bodyScale
    torsoEffectHeight = ToontownGlobals.torsoHeightDict[toon.style.torso] * bodyScale / 2 + legsHeight
    legsEffectHeight = legsHeight / 2
    effectX = headEffect.getX()
    effectY = headEffect.getY()
    headEffect.setPos(effectX, effectY - 1.5, headEffectHeight)
    torsoEffect.setPos(effectX, effectY - 1, torsoEffectHeight)
    legsEffect.setPos(effectX, effectY - 0.6, legsEffectHeight)
    partDelay = 2.5
    headTrack = getPartTrack(headEffect, partDelay + 0, 0.5, [headEffect, toon, 0])
    torsoTrack = getPartTrack(torsoEffect, partDelay + 1.1, 0.5, [torsoEffect, toon, 0])
    legsTrack = getPartTrack(legsEffect, partDelay + 2.2, 0.5, [legsEffect, toon, 0])

    def hideParts(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(Func(nextPart.setTransparency, 1))
            track.append(LerpFunctionInterval(nextPart.setAlphaScale, fromData=1, toData=0, duration=0.2))

        return track

    def showParts(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(Func(nextPart.clearColorScale))
            track.append(Func(nextPart.clearTransparency))

        return track

    soundTrack = getSoundTrack('SA_rubout.ogg', delay=1.7, node=suit)
    if dmg > 0:
        hideTrack.append(Wait(2.2))
        hideTrack.append(Func(battle.movie.needRestoreColor))
        hideTrack.append(hideParts(headParts))
        hideTrack.append(Wait(0.4))
        hideTrack.append(hideParts(torsoParts))
        hideTrack.append(Wait(0.4))
        hideTrack.append(hideParts(legsParts))
        hideTrack.append(Wait(1))
        hideTrack.append(showParts(headParts))
        hideTrack.append(showParts(torsoParts))
        hideTrack.append(showParts(legsParts))
        hideTrack.append(Func(battle.movie.clearRestoreColor))
        return Parallel(suitTrack, toonTrack, padPropTrack, pencilPropTrack, soundTrack, hideTrack, headTrack, torsoTrack, legsTrack)
    return Parallel(suitTrack, toonTrack, padPropTrack, pencilPropTrack, soundTrack)


def doFingerWag(attack):
    suit = attack['suit']
    battle = attack['battle']
    BattleParticles.loadParticles()
    particleEffect = BattleParticles.createParticleEffect('FingerWag')
    BattleParticles.setEffectTexture(particleEffect, 'blah', color=Vec4(0.55, 0, 0.55, 1))
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        partDelay = 1.3
        damageDelay = 2.7
        dodgeDelay = 1.7
    else:
        if suitType == 'b':
            partDelay = 1.3
            damageDelay = 2.7
            dodgeDelay = 1.8
        else:
            if suitType == 'c':
                partDelay = 1.3
                damageDelay = 2.7
                dodgeDelay = 2.0
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(particleEffect, partDelay, 2, [particleEffect, suit, 0])
    suitName = attack['suitName']
    if suitName == 'mm':
        particleEffect.setPos(0.167, 1.5, 2.731)
    else:
        if suitName == 'tw':
            particleEffect.setPos(0.167, 1.8, 5)
            particleEffect.setHpr(-90.0, -60.0, 180.0)
        else:
            if suitName == 'pp':
                particleEffect.setPos(0.167, 1, 4.1)
            else:
                if suitName == 'bs':
                    particleEffect.setPos(0.167, 1, 5.1)
                else:
                    if suitName == 'bw':
                        particleEffect.setPos(0.167, 1.9, suit.getHeight() - 1.8)
                        particleEffect.setP(-110)
    toonTrack = getToonTrack(attack, damageDelay, ['slip-backward'], dodgeDelay, ['sidestep'])
    soundTrack = getSoundTrack('SA_finger_wag.ogg', delay=1.3, node=suit)
    return Parallel(suitTrack, toonTrack, partTrack, soundTrack)


def doWriteOff(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    pad = globalPropPool.getProp('pad')
    pencil = globalPropPool.getProp('pencil')
    BattleParticles.loadParticles()
    checkmark = MovieUtil.copyProp(BattleParticles.getParticle('checkmark'))
    checkmark.setBillboardPointEye()
    suitTrack = getSuitTrack(attack)
    padPosPoints = [Point3(-0.25, 1.38, -0.08), VBase3(-19.078, -6.603, -171.594)]
    padPropTrack = getPropTrack(pad, suit.getLeftHand(), padPosPoints, 0.5, 2.57, Point3(1.89, 1.89, 1.89))
    missPoint = lambda checkmark=checkmark, toon=toon: __toonMissPoint(checkmark, toon)
    pencilPosPoints = [Point3(-0.47, 1.08, 0.28), VBase3(21.045, 12.702, -176.374)]
    extraArgsForShowProp = [pencil, suit.getRightHand()]
    extraArgsForShowProp.extend(pencilPosPoints)
    pencilPropTrack = Sequence(Wait(0.5), Func(__showProp, *extraArgsForShowProp), LerpScaleInterval(pencil, 0.5, Point3(1.5, 1.5, 1.5), startScale=Point3(0.01)), Wait(2), Func(battle.movie.needRestoreRenderProp, checkmark), Func(checkmark.reparentTo, render), Func(checkmark.setScale, 1.6), Func(checkmark.setPosHpr, pencil, 0, 0, 0, 0, 0, 0), Func(checkmark.setP, 0), Func(checkmark.setR, 0))
    pencilPropTrack.append(getPropThrowTrack(attack, checkmark, [__toonFacePoint(toon)], [missPoint]))
    pencilPropTrack.append(Func(MovieUtil.removeProp, checkmark))
    pencilPropTrack.append(Func(battle.movie.clearRenderProp, checkmark))
    pencilPropTrack.append(Wait(0.3))
    pencilPropTrack.append(LerpScaleInterval(pencil, 0.5, MovieUtil.PNT3_NEARZERO))
    pencilPropTrack.append(Func(MovieUtil.removeProp, pencil))
    toonTrack = getToonTrack(attack, 3.4, ['slip-forward'], 2.4, ['sidestep'])
    soundTrack = Sequence(Wait(2.3), SoundInterval(globalBattleSoundCache.getSound('SA_writeoff_pen_only.ogg'), duration=0.9, node=suit), SoundInterval(globalBattleSoundCache.getSound('SA_writeoff_ding_only.ogg'), node=suit))
    return Parallel(suitTrack, toonTrack, padPropTrack, pencilPropTrack, soundTrack)


def doRubberStamp(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    suitTrack = getSuitTrack(attack)
    stamp = globalPropPool.getProp('rubber-stamp')
    pad = globalPropPool.getProp('pad')
    cancelled = __makeCancelledNodePath()
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        padPosPoints = [
         Point3(-0.65, 0.83, -0.04), VBase3(5.625, 4.456, -165.125)]
        stampPosPoints = [Point3(-0.64, -0.17, -0.03), MovieUtil.PNT3_ZERO]
    else:
        if suitType == 'c':
            padPosPoints = [
             Point3(0.19, -0.55, -0.21), VBase3(-166.76, -4.001, -1.658)]
            stampPosPoints = [Point3(-0.64, -0.08, 0.11), MovieUtil.PNT3_ZERO]
        else:
            padPosPoints = [
             Point3(-0.65, 0.83, -0.04), VBase3(5.625, 4.456, -165.125)]
            stampPosPoints = [Point3(-0.64, -0.17, -0.03), MovieUtil.PNT3_ZERO]
    padPropTrack = getPropTrack(pad, suit.getLeftHand(), padPosPoints, 1e-06, 3.2)
    missPoint = lambda cancelled=cancelled, toon=toon: __toonMissPoint(cancelled, toon)
    propTrack = Sequence(Func(__showProp, stamp, suit.getRightHand(), stampPosPoints[0], stampPosPoints[1]), LerpScaleInterval(stamp, 0.5, MovieUtil.PNT3_ONE), Wait(2.6), Func(battle.movie.needRestoreRenderProp, cancelled), Func(cancelled.reparentTo, render), Func(cancelled.setScale, 0.6), Func(cancelled.setPosHpr, stamp, 0.81, -1.11, -0.16, 0, 0, 90), Func(cancelled.setP, 0), Func(cancelled.setR, 0))
    propTrack.append(getPropThrowTrack(attack, cancelled, [__toonFacePoint(toon)], [missPoint]))
    propTrack.append(Func(MovieUtil.removeProp, cancelled))
    propTrack.append(Func(battle.movie.clearRenderProp, cancelled))
    propTrack.append(Wait(0.3))
    propTrack.append(LerpScaleInterval(stamp, 0.5, MovieUtil.PNT3_NEARZERO))
    propTrack.append(Func(MovieUtil.removeProp, stamp))
    toonTrack = getToonTrack(attack, 3.4, ['conked'], 1.9, ['sidestep'])
    soundTrack = getSoundTrack('SA_rubber_stamp.ogg', delay=1.3, duration=1.1, node=suit)
    return Parallel(suitTrack, toonTrack, propTrack, padPropTrack, soundTrack)


def doRazzleDazzle(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    hitSuit = dmg > 0
    sign = globalPropPool.getProp('smile')
    BattleParticles.loadParticles()
    particleEffect = BattleParticles.createParticleEffect('Smile')
    suitTrack = getSuitTrack(attack)
    signPosPoints = [Point3(0.0, -0.42, -0.04), VBase3(105.715, 73.977, 65.932)]
    if hitSuit:
        hitPoint = lambda toon=toon: __toonFacePoint(toon)
    else:
        hitPoint = lambda particleEffect=particleEffect, toon=toon, suit=suit: __toonMissPoint(particleEffect, toon, parent=suit.getRightHand())
    signPropTrack = Sequence(Wait(0.5), Func(__showProp, sign, suit.getRightHand(), signPosPoints[0], signPosPoints[1]), LerpScaleInterval(sign, 0.5, Point3(1.39, 1.39, 1.39)), Wait(0.5), Func(battle.movie.needRestoreParticleEffect, particleEffect), Func(particleEffect.start, sign), Func(particleEffect.wrtReparentTo, render), LerpPosInterval(particleEffect, 2.0, pos=hitPoint), Func(particleEffect.cleanup), Func(battle.movie.clearRestoreParticleEffect, particleEffect))
    signPropAnimTrack = ActorInterval(sign, 'smile', duration=4, startTime=0)
    toonTrack = getToonTrack(attack, 2.6, ['cringe'], 1.9, ['sidestep'])
    soundTrack = getSoundTrack('SA_razzle_dazzle.ogg', delay=1.6, node=suit)
    return Sequence(Parallel(suitTrack, signPropTrack, signPropAnimTrack, toonTrack, soundTrack), Func(MovieUtil.removeProp, sign))


def doSynergy(attack):
    suit = attack['suit']
    battle = attack['battle']
    targets = attack['target']
    damageDelay = 1.7
    hitAtleastOneToon = 0
    for t in targets:
        if t['hp'] > 0:
            hitAtleastOneToon = 1

    particleEffect = BattleParticles.createParticleEffect('Synergy')
    waterfallEffect = BattleParticles.createParticleEffect(file='synergyWaterfall')
    suitTrack = getSuitAnimTrack(attack)
    partTrack = getPartTrack(particleEffect, 1.0, 1.9, [particleEffect, suit, 0])
    waterfallTrack = getPartTrack(waterfallEffect, 0.8, 1.9, [waterfallEffect, suit, 0])
    damageAnims = [['slip-forward']]
    dodgeAnims = []
    dodgeAnims.append(['jump',
     0.01,
     0,
     0.6])
    dodgeAnims.extend(getSplicedLerpAnims('jump', 0.31, 1.3, startTime=0.6))
    dodgeAnims.append(['jump', 0, 0.91])
    toonTracks = getToonTracks(attack, damageDelay=damageDelay, damageAnimNames=['slip-forward'], dodgeDelay=0.91, splicedDodgeAnims=dodgeAnims, showMissedExtraTime=1.0)
    synergySoundTrack = Sequence(Wait(0.9), SoundInterval(globalBattleSoundCache.getSound('SA_synergy.ogg'), node=suit))
    if hitAtleastOneToon > 0:
        fallingSoundTrack = Sequence(Wait(damageDelay + 0.5), SoundInterval(globalBattleSoundCache.getSound('Toon_bodyfall_synergy.ogg'), node=suit))
        return Parallel(suitTrack, partTrack, waterfallTrack, synergySoundTrack, fallingSoundTrack, toonTracks)
    return Parallel(suitTrack, partTrack, waterfallTrack, synergySoundTrack, toonTracks)


def doTeeOff(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    club = globalPropPool.getProp('golf-club')
    ball = globalPropPool.getProp('golf-ball')
    suitTrack = getSuitTrack(attack)
    clubPosPoints = [MovieUtil.PNT3_ZERO, VBase3(63.097, 43.988, -18.435)]
    clubPropTrack = getPropTrack(club, suit.getLeftHand(), clubPosPoints, 0.5, 5.2, Point3(1.1, 1.1, 1.1))
    suitName = attack['suitName']
    if suitName == 'ym':
        ballPosPoints = [
         Point3(2.1, 0, 0.1)]
    else:
        if suitName == 'tbc':
            ballPosPoints = [
             Point3(4.1, 0, 0.1)]
        else:
            if suitName == 'm':
                ballPosPoints = [
                 Point3(3.2, 0, 0.1)]
            else:
                if suitName == 'rb' or suitName == 'sm':
                    ballPosPoints = [
                     Point3(4.2, 0, 0.1)]
                else:
                    ballPosPoints = [
                     Point3(2.1, 0, 0.1)]
    ballPropTrack = Sequence(getPropAppearTrack(ball, suit, ballPosPoints, 1.7, Point3(1.5, 1.5, 1.5)), Func(battle.movie.needRestoreRenderProp, ball), Func(ball.wrtReparentTo, render), Wait(2.15))
    missPoint = lambda ball=ball, toon=toon: __toonMissPoint(ball, toon)
    ballPropTrack.append(getPropThrowTrack(attack, ball, [__toonFacePoint(toon)], [missPoint]))
    ballPropTrack.append(Func(battle.movie.clearRenderProp, ball))
    dodgeDelay = suitTrack.getDuration() - 4.35
    toonTrack = getToonTrack(attack, suitTrack.getDuration() - 2.25, ['conked'], dodgeDelay, ['duck'], showMissedExtraTime=1.7)
    soundTrack = getSoundTrack('SA_tee_off.ogg', delay=4.1, node=suit)
    return Parallel(suitTrack, toonTrack, clubPropTrack, ballPropTrack, soundTrack)


def doBrainStorm(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    BattleParticles.loadParticles()
    snowEffect = BattleParticles.createParticleEffect('BrainStorm')
    snowEffect2 = BattleParticles.createParticleEffect('BrainStorm')
    snowEffect3 = BattleParticles.createParticleEffect('BrainStorm')
    effectColor = Vec4(0.65, 0.79, 0.93, 0.85)
    BattleParticles.setEffectTexture(snowEffect, 'brainstorm-box', color=effectColor)
    BattleParticles.setEffectTexture(snowEffect2, 'brainstorm-env', color=effectColor)
    BattleParticles.setEffectTexture(snowEffect3, 'brainstorm-track', color=effectColor)
    cloud = globalPropPool.getProp('stormcloud')
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        partDelay = 1.2
        damageDelay = 4.5
        dodgeDelay = 3.3
    else:
        if suitType == 'b':
            partDelay = 1.2
            damageDelay = 4.5
            dodgeDelay = 3.3
        else:
            if suitType == 'c':
                partDelay = 1.2
                damageDelay = 4.5
                dodgeDelay = 3.3
    suitTrack = getSuitTrack(attack, delay=0.9)
    initialCloudHeight = suit.height + 3
    cloudPosPoints = [Point3(0, 3, initialCloudHeight), VBase3(180, 0, 0)]
    cloudPropTrack = Sequence()
    cloudPropTrack.append(Func(cloud.pose, 'stormcloud', 0))
    cloudPropTrack.append(getPropAppearTrack(cloud, suit, cloudPosPoints, 1e-06, Point3(3, 3, 3), scaleUpTime=0.7))
    cloudPropTrack.append(Func(battle.movie.needRestoreRenderProp, cloud))
    cloudPropTrack.append(Func(cloud.wrtReparentTo, render))
    targetPoint = __toonFacePoint(toon)
    targetPoint.setZ(targetPoint[2] + 3)
    cloudPropTrack.append(Wait(1.1))
    cloudPropTrack.append(LerpPosInterval(cloud, 1, pos=targetPoint))
    cloudPropTrack.append(Wait(partDelay))
    cloudPropTrack.append(Parallel(ParticleInterval(snowEffect, cloud, worldRelative=0, duration=2.2, cleanup=True), Sequence(Wait(0.5), ParticleInterval(snowEffect2, cloud, worldRelative=0, duration=1.7, cleanup=True)), Sequence(Wait(1.0), ParticleInterval(snowEffect3, cloud, worldRelative=0, duration=1.2, cleanup=True)), Sequence(ActorInterval(cloud, 'stormcloud', startTime=3, duration=0.5), ActorInterval(cloud, 'stormcloud', startTime=2.5, duration=0.5), ActorInterval(cloud, 'stormcloud', startTime=1, duration=1.5))))
    cloudPropTrack.append(Wait(0.4))
    cloudPropTrack.append(LerpScaleInterval(cloud, 0.5, MovieUtil.PNT3_NEARZERO))
    cloudPropTrack.append(Func(MovieUtil.removeProp, cloud))
    cloudPropTrack.append(Func(battle.movie.clearRenderProp, cloud))
    damageAnims = [
     ['cringe',
      0.01,
      0.4,
      0.8], ['duck', 1e-06, 1.6]]
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, dodgeAnimNames=['sidestep'], showMissedExtraTime=1.1)
    soundTrack = getSoundTrack('SA_brainstorm.ogg', delay=2.6, node=suit)
    return Parallel(suitTrack, toonTrack, cloudPropTrack, soundTrack)


def doBuzzWord(attack):
    suit = attack['suit']
    target = attack['target']
    toon = target['toon']
    battle = attack['battle']
    BattleParticles.loadParticles()
    particleEffects = []
    texturesList = ['buzzwords-crash',
     'buzzwords-inc',
     'buzzwords-main',
     'buzzwords-over',
     'buzzwords-syn']
    for i in range(0, 5):
        effect = BattleParticles.createParticleEffect('BuzzWord')
        if random.random() > 0.5:
            BattleParticles.setEffectTexture(effect, texturesList[i], color=Vec4(1, 0.94, 0.02, 1))
        else:
            BattleParticles.setEffectTexture(effect, texturesList[i], color=Vec4(0, 0, 0, 1))
        particleEffects.append(effect)

    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        partDelay = 4.0
        partDuration = 2.2
        damageDelay = 4.5
        dodgeDelay = 3.8
    else:
        if suitType == 'b':
            partDelay = 1.3
            partDuration = 2
            damageDelay = 2.5
            dodgeDelay = 1.8
        else:
            if suitType == 'c':
                partDelay = 4.0
                partDuration = 2.2
                damageDelay = 4.5
                dodgeDelay = 3.8
    suitName = suit.getStyleName()
    if suitName == 'm':
        for effect in particleEffects:
            effect.setPos(0, 2.8, suit.getHeight() - 2.5)
            effect.setHpr(0, -20, 0)

    else:
        if suitName == 'mm':
            for effect in particleEffects:
                effect.setPos(0, 2.1, suit.getHeight() - 0.8)

    suitTrack = getSuitTrack(attack)
    particleTracks = []
    for effect in particleEffects:
        particleTracks.append(getPartTrack(effect, partDelay, partDuration, [effect, suit, 0]))

    toonTrack = getToonTrack(attack, damageDelay=damageDelay, damageAnimNames=['cringe'], splicedDodgeAnims=[['duck', dodgeDelay, 1.4]], showMissedExtraTime=dodgeDelay + 0.5)
    soundTrack = getSoundTrack('SA_buzz_word.ogg', delay=3.9, node=suit)
    return Parallel(suitTrack, toonTrack, soundTrack, *particleTracks)


def doDemotion(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    BattleParticles.loadParticles()
    sprayEffect = BattleParticles.createParticleEffect('DemotionSpray')
    freezeEffect = BattleParticles.createParticleEffect('DemotionFreeze')
    unFreezeEffect = BattleParticles.createParticleEffect(file='demotionUnFreeze')
    BattleParticles.setEffectTexture(sprayEffect, 'snow-particle')
    BattleParticles.setEffectTexture(freezeEffect, 'snow-particle')
    BattleParticles.setEffectTexture(unFreezeEffect, 'snow-particle')
    facePoint = __toonFacePoint(toon)
    freezeEffect.setPos(0, 0, facePoint.getZ())
    unFreezeEffect.setPos(0, 0, facePoint.getZ())
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(sprayEffect, 0.7, 1.1, [sprayEffect, suit, 0])
    partTrack2 = getPartTrack(freezeEffect, 1.4, 2.9, [freezeEffect, toon, 0])
    partTrack3 = getPartTrack(unFreezeEffect, 6.65, 0.5, [unFreezeEffect, toon, 0])
    dodgeAnims = [['duck', 1e-06, 0.8]]
    damageAnims = []
    damageAnims.append(['cringe',
     0.01,
     0,
     0.5])
    damageAnims.extend(getSplicedLerpAnims('cringe', 0.4, 0.5, startTime=0.5))
    damageAnims.extend(getSplicedLerpAnims('cringe', 0.3, 0.5, startTime=0.9))
    damageAnims.extend(getSplicedLerpAnims('cringe', 0.3, 0.6, startTime=1.2))
    damageAnims.append(['cringe', 2.6, 1.5])
    toonTrack = getToonTrack(attack, damageDelay=1.0, splicedDamageAnims=damageAnims, splicedDodgeAnims=dodgeAnims, showMissedExtraTime=1.6, showDamageExtraTime=1.3)
    soundTrack = getSoundTrack('SA_demotion.ogg', delay=1.2, node=suit)
    if dmg > 0:
        return Parallel(suitTrack, toonTrack, soundTrack, partTrack, partTrack2, partTrack3)
    return Parallel(suitTrack, toonTrack, soundTrack, partTrack)


def doCanned(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    dmg = target['hp']
    toon = target['toon']
    hips = toon.getHipsParts()
    propDelay = 0.8
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'c':
        suitDelay = 1.13
        dodgeDelay = 3.1
    else:
        suitDelay = 1.83
        dodgeDelay = 3.6
    throwDuration = 1.5
    can = globalPropPool.getProp('can')
    scale = 26
    torso = toon.style.torso
    torso = torso[0]
    if torso == 's':
        scaleUpPoint = Point3(scale * 2.63, scale * 2.63, scale * 1.9975)
    else:
        if torso == 'm':
            scaleUpPoint = Point3(scale * 2.63, scale * 2.63, scale * 1.7975)
        else:
            if torso == 'l':
                scaleUpPoint = Point3(scale * 2.63, scale * 2.63, scale * 2.31)
    canHpr = VBase3(-173.47, -0.42, 162.09)
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(-0.14, 0.15, 0.08), VBase3(-10.584, 11.945, -161.684)]
    throwTrack = Sequence(getPropAppearTrack(can, suit.getRightHand(), posPoints, propDelay, Point3(6, 6, 6), scaleUpTime=0.5))
    propDelay = propDelay + 0.5
    throwTrack.append(Wait(suitDelay))
    hitPoint = toon.getPos(battle)
    hitPoint.setX(hitPoint.getX() + 1.1)
    hitPoint.setY(hitPoint.getY() - 0.5)
    hitPoint.setZ(hitPoint.getZ() + toon.height + 1.1)
    throwTrack.append(Func(battle.movie.needRestoreRenderProp, can))
    throwTrack.append(getThrowTrack(can, hitPoint, duration=throwDuration, parent=battle))
    if dmg > 0:
        can2 = MovieUtil.copyProp(can)
        hips1 = hips.getPath(2)
        hips2 = hips.getPath(1)
        can2Point = Point3(hitPoint.getX(), hitPoint.getY() + 6.4, hitPoint.getZ())
        can2.setPos(can2Point)
        can2.setScale(scaleUpPoint)
        can2.setHpr(canHpr)
        throwTrack.append(Func(battle.movie.needRestoreHips))
        throwTrack.append(Func(can.wrtReparentTo, hips1))
        throwTrack.append(Func(can2.reparentTo, hips2))
        throwTrack.append(Wait(2.4))
        throwTrack.append(Func(MovieUtil.removeProp, can2))
        throwTrack.append(Func(battle.movie.clearRestoreHips))
        scaleTrack = Sequence(Wait(propDelay + suitDelay), LerpScaleInterval(can, throwDuration, scaleUpPoint))
        hprTrack = Sequence(Wait(propDelay + suitDelay), LerpHprInterval(can, throwDuration, canHpr))
        soundTrack = Sequence(Wait(2.6), SoundInterval(globalBattleSoundCache.getSound('SA_canned_tossup_only.ogg'), node=suit), SoundInterval(globalBattleSoundCache.getSound('SA_canned_impact_only.ogg'), node=suit))
    else:
        land = toon.getPos(battle)
        land.setZ(land.getZ() + 0.7)
        bouncePoint1 = Point3(land.getX(), land.getY() - 1.5, land.getZ() + 2.5)
        bouncePoint2 = Point3(land.getX(), land.getY() - 2.1, land.getZ() - 0.2)
        bouncePoint3 = Point3(land.getX(), land.getY() - 3.1, land.getZ() + 1.5)
        bouncePoint4 = Point3(land.getX(), land.getY() - 4.1, land.getZ() + 0.3)
        throwTrack.append(LerpPosInterval(can, 0.4, land))
        throwTrack.append(LerpPosInterval(can, 0.4, bouncePoint1))
        throwTrack.append(LerpPosInterval(can, 0.3, bouncePoint2))
        throwTrack.append(LerpPosInterval(can, 0.3, bouncePoint3))
        throwTrack.append(LerpPosInterval(can, 0.3, bouncePoint4))
        throwTrack.append(Wait(1.1))
        throwTrack.append(LerpScaleInterval(can, 0.3, MovieUtil.PNT3_NEARZERO))
        scaleTrack = Sequence(Wait(propDelay + suitDelay), LerpScaleInterval(can, throwDuration, Point3(11, 11, 11)))
        hprTrack = Sequence(Wait(propDelay + suitDelay), LerpHprInterval(can, throwDuration, canHpr), Wait(0.4), LerpHprInterval(can, 0.4, Point3(83.27, 19.52, -177.92)), LerpHprInterval(can, 0.3, Point3(95.24, -72.09, 88.65)), LerpHprInterval(can, 0.2, Point3(-96.34, -2.63, 179.89)))
        soundTrack = getSoundTrack('SA_canned_tossup_only.ogg', delay=2.6, node=suit)
    canTrack = Sequence(Parallel(throwTrack, scaleTrack, hprTrack), Func(MovieUtil.removeProp, can), Func(battle.movie.clearRenderProp, can))
    damageAnims = [
     ['struggle',
      propDelay + suitDelay + throwDuration,
      0.01,
      0.7], ['slip-backward', 0.01, 0.45]]
    toonTrack = getToonTrack(attack, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, dodgeAnimNames=['sidestep'], showDamageExtraTime=propDelay + suitDelay + 2.4)
    return Parallel(suitTrack, toonTrack, canTrack, soundTrack)


def doDownsize(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    damageDelay = 2.3
    sprayEffect = BattleParticles.createParticleEffect(file='downsizeSpray')
    cloudEffect = BattleParticles.createParticleEffect(file='downsizeCloud')
    toonPos = toon.getPos(toon)
    cloudPos = Point3(toonPos.getX(), toonPos.getY(), toonPos.getZ() + toon.getHeight() * 0.55)
    cloudEffect.setPos(cloudPos)
    suitTrack = getSuitTrack(attack)
    sprayTrack = getPartTrack(sprayEffect, 1.0, 1.28, [sprayEffect, suit, 0])
    cloudTrack = getPartTrack(cloudEffect, 2.1, 1.9, [cloudEffect, toon, 0])
    if dmg > 0:
        initialScale = toon.getScale()
        downScale = Vec3(0.4, 0.4, 0.4)
        shrinkTrack = Sequence(Wait(damageDelay + 0.5), Func(battle.movie.needRestoreToonScale), LerpScaleInterval(toon, 1.0, downScale * 1.1), LerpScaleInterval(toon, 0.1, downScale * 0.9), LerpScaleInterval(toon, 0.1, downScale * 1.05), LerpScaleInterval(toon, 0.1, downScale * 0.95), LerpScaleInterval(toon, 0.1, downScale), Wait(2.1), LerpScaleInterval(toon, 0.5, initialScale * 1.5), LerpScaleInterval(toon, 0.15, initialScale * 0.5), LerpScaleInterval(toon, 0.15, initialScale * 1.2), LerpScaleInterval(toon, 0.15, initialScale * 0.8), LerpScaleInterval(toon, 0.15, initialScale), Func(battle.movie.clearRestoreToonScale))
    damageAnims = []
    damageAnims.append(['juggle',
     0.01,
     0.87,
     0.5])
    damageAnims.append(['lose',
     0.01,
     2.17,
     0.93])
    damageAnims.append(['lose',
     0.01,
     3.1,
     -0.93])
    damageAnims.append(['struggle',
     0.01,
     0.8,
     1.8])
    damageAnims.append(['sidestep-right',
     0.01,
     2.97,
     1.49])
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=0.6, dodgeAnimNames=['sidestep'])
    if dmg > 0:
        return Parallel(suitTrack, sprayTrack, cloudTrack, shrinkTrack, toonTrack)
    return Parallel(suitTrack, sprayTrack, toonTrack)


def doPinkSlip(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    paper = globalPropPool.getProp('pink-slip')
    throwDelay = 3.03
    throwDuration = 0.5
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(0.07, -0.06, -0.18), VBase3(-172.075, -26.715, -89.131)]
    paperAppearTrack = Sequence(getPropAppearTrack(paper, suit.getRightHand(), posPoints, 0.8, Point3(8, 8, 8), scaleUpTime=0.5))
    paperAppearTrack.append(Wait(1.73))
    hitPoint = __toonGroundPoint(attack, toon, 0.2, parent=battle)
    paperAppearTrack.append(Func(battle.movie.needRestoreRenderProp, paper))
    paperAppearTrack.append(Func(paper.wrtReparentTo, battle))
    paperAppearTrack.append(LerpPosInterval(paper, throwDuration, hitPoint))
    if dmg > 0:
        paperPause = 0.01
        slidePoint = Point3(hitPoint.getX(), hitPoint.getY() - 5, hitPoint.getZ() + 4)
        landPoint = Point3(hitPoint.getX(), hitPoint.getY() - 5, hitPoint.getZ())
        paperAppearTrack.append(Wait(paperPause))
        paperAppearTrack.append(LerpPosInterval(paper, 0.2, slidePoint))
        paperAppearTrack.append(LerpPosInterval(paper, 1.1, landPoint))
        paperSpinTrack = Sequence(Wait(throwDelay), LerpHprInterval(paper, throwDuration, VBase3(300, 0, 0)), Wait(paperPause), LerpHprInterval(paper, 1.3, VBase3(-200, 100, 100)))
    else:
        slidePoint = Point3(hitPoint.getX(), hitPoint.getY() - 5, hitPoint.getZ())
        paperAppearTrack.append(LerpPosInterval(paper, 0.5, slidePoint))
        paperSpinTrack = Sequence(Wait(throwDelay), LerpHprInterval(paper, throwDuration, VBase3(300, 0, 0)), LerpHprInterval(paper, 0.5, VBase3(10, 0, 0)))
    propTrack = Sequence()
    propTrack.append(Parallel(paperAppearTrack, paperSpinTrack))
    propTrack.append(LerpScaleInterval(paper, 0.4, MovieUtil.PNT3_NEARZERO))
    propTrack.append(Func(MovieUtil.removeProp, paper))
    propTrack.append(Func(battle.movie.clearRenderProp, paper))
    damageAnims = [
     ['jump',
      0.01,
      0.3,
      0.7], ['slip-forward', 0.01]]
    toonTrack = getToonTrack(attack, damageDelay=2.81, splicedDamageAnims=damageAnims, dodgeDelay=2.8, dodgeAnimNames=['jump'], showDamageExtraTime=0.9)
    soundTrack = getSoundTrack('SA_pink_slip.ogg', delay=2.9, duration=1.1, node=suit)
    return Parallel(suitTrack, toonTrack, propTrack, soundTrack)


def doReOrg(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    damageDelay = 1.7
    attackDelay = 1.7
    sprayEffect = BattleParticles.createParticleEffect(file='reorgSpray')
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(sprayEffect, 1.0, 1.9, [sprayEffect, suit, 0])
    if dmg > 0:
        headParts = toon.getHeadParts()
        print '***********headParts pos=', headParts[0].getPos()
        print '***********headParts hpr=', headParts[0].getHpr()
        headTracks = Parallel()
        for partNum in range(0, headParts.getNumPaths()):
            part = headParts.getPath(partNum)
            x = part.getX()
            y = part.getY()
            z = part.getZ()
            h = part.getH()
            p = part.getP()
            r = part.getR()
            headTracks.append(Sequence(Wait(attackDelay), LerpPosInterval(part, 0.1, Point3(x - 0.2, y, z - 0.03)), LerpPosInterval(part, 0.1, Point3(x + 0.4, y, z - 0.03)), LerpPosInterval(part, 0.1, Point3(x - 0.4, y, z - 0.03)), LerpPosInterval(part, 0.1, Point3(x + 0.4, y, z - 0.03)), LerpPosInterval(part, 0.1, Point3(x - 0.2, y, z - 0.04)), LerpPosInterval(part, 0.25, Point3(x, y, z + 2.2)), LerpHprInterval(part, 0.4, VBase3(360, 0, 180)), LerpPosInterval(part, 0.3, Point3(x, y, z + 3.1)), LerpPosInterval(part, 0.15, Point3(x, y, z + 0.3)), Wait(0.15), LerpHprInterval(part, 0.6, VBase3(-745, 0, 180), startHpr=VBase3(0, 0, 180)), LerpHprInterval(part, 0.8, VBase3(25, 0, 180), startHpr=VBase3(0, 0, 180)), LerpPosInterval(part, 0.15, Point3(x, y, z + 1)), LerpHprInterval(part, 0.3, VBase3(h, p, r)), Wait(0.2), LerpPosInterval(part, 0.1, Point3(x, y, z)), Wait(0.9)))

        def getChestTrack(part, attackDelay=attackDelay):
            origScale = part.getScale()
            return Sequence(Wait(attackDelay), LerpHprInterval(part, 1.1, VBase3(180, 0, 0)), Wait(1.1), LerpHprInterval(part, 1.1, part.getHpr()))

        chestTracks = Parallel()
        arms = toon.findAllMatches('**/arms')
        sleeves = toon.findAllMatches('**/sleeves')
        hands = toon.findAllMatches('**/hands')
        print '*************arms hpr=', arms[0].getHpr()
        for partNum in range(0, arms.getNumPaths()):
            chestTracks.append(getChestTrack(arms.getPath(partNum)))
            chestTracks.append(getChestTrack(sleeves.getPath(partNum)))
            chestTracks.append(getChestTrack(hands.getPath(partNum)))

    damageAnims = [
     [
      'neutral',
      0.01,
      0.01,
      0.5],
     ['juggle',
      0.01,
      0.01,
      1.48], ['think', 0.01, 2.28]]
    dodgeAnims = []
    dodgeAnims.append(['think',
     0.01,
     0,
     0.6])
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=0.01, dodgeAnimNames=['duck'], showDamageExtraTime=2.1, showMissedExtraTime=2.0)
    if dmg > 0:
        return Parallel(suitTrack, partTrack, toonTrack, headTracks, chestTracks)
    else:
        return Parallel(suitTrack, partTrack, toonTrack)


def doSacked(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    dmg = target['hp']
    toon = target['toon']
    hips = toon.getHipsParts()
    propDelay = 0.85
    suitDelay = 1.93
    throwDuration = 0.9
    sack = globalPropPool.getProp('sandbag')
    initialScale = Point3(0.65, 1.47, 1.28)
    scaleUpPoint = Point3(1.05, 1.67, 0.98) * 4.1
    sackHpr = VBase3(-154.33, -6.33, 163.8)
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(0.51, -2.03, -0.73), VBase3(90.0, -24.98, 77.73)]
    sackAppearTrack = Sequence(getPropAppearTrack(sack, suit.getRightHand(), posPoints, propDelay, initialScale, scaleUpTime=0.2))
    propDelay = propDelay + 0.2
    sackAppearTrack.append(Wait(suitDelay))
    hitPoint = toon.getPos(battle)
    if dmg > 0:
        hitPoint.setX(hitPoint.getX() + 2.1)
        hitPoint.setY(hitPoint.getY() + 0.9)
        hitPoint.setZ(hitPoint.getZ() + toon.height + 1.2)
    else:
        hitPoint.setZ(hitPoint.getZ() - 0.2)
    sackAppearTrack.append(Func(battle.movie.needRestoreRenderProp, sack))
    sackAppearTrack.append(getThrowTrack(sack, hitPoint, duration=throwDuration, parent=battle))
    if dmg > 0:
        sack2 = MovieUtil.copyProp(sack)
        hips1 = hips.getPath(2)
        hips2 = hips.getPath(1)
        sack2.hide()
        sack2.reparentTo(battle)
        sack2.setPos(Point3(hitPoint.getX(), hitPoint.getY(), hitPoint.getZ()))
        sack2.setScale(scaleUpPoint)
        sack2.setHpr(sackHpr)
        sackAppearTrack.append(Func(battle.movie.needRestoreHips))
        sackAppearTrack.append(Func(sack.wrtReparentTo, hips1))
        sackAppearTrack.append(Func(sack2.show))
        sackAppearTrack.append(Func(sack2.wrtReparentTo, hips2))
        sackAppearTrack.append(Wait(2.4))
        sackAppearTrack.append(Func(MovieUtil.removeProp, sack2))
        sackAppearTrack.append(Func(battle.movie.clearRestoreHips))
        scaleTrack = Sequence(Wait(propDelay + suitDelay), LerpScaleInterval(sack, throwDuration, scaleUpPoint), Wait(1.8), LerpScaleInterval(sack, 0.3, MovieUtil.PNT3_NEARZERO))
        hprTrack = Sequence(Wait(propDelay + suitDelay), LerpHprInterval(sack, throwDuration, sackHpr))
        sackTrack = Sequence(Parallel(sackAppearTrack, scaleTrack, hprTrack), Func(MovieUtil.removeProp, sack), Func(battle.movie.clearRenderProp, sack))
    else:
        sackAppearTrack.append(Wait(1.1))
        sackAppearTrack.append(LerpScaleInterval(sack, 0.3, MovieUtil.PNT3_NEARZERO))
        sackTrack = Sequence(sackAppearTrack, Func(MovieUtil.removeProp, sack), Func(battle.movie.clearRenderProp, sack))
    damageAnims = [
     [
      'struggle',
      0.01,
      0.01,
      0.7], ['slip-backward', 0.01, 0.45]]
    toonTrack = getToonTrack(attack, damageDelay=propDelay + suitDelay + throwDuration, splicedDamageAnims=damageAnims, dodgeDelay=3.0, dodgeAnimNames=['sidestep'], showDamageExtraTime=1.8, showMissedExtraTime=0.8)
    return Parallel(suitTrack, toonTrack, sackTrack)


def doGlowerPower(attack):
    suit = attack['suit']
    battle = attack['battle']
    leftKnives = []
    rightKnives = []
    for i in range(0, 3):
        leftKnives.append(globalPropPool.getProp('dagger'))
        rightKnives.append(globalPropPool.getProp('dagger'))

    suitTrack = getSuitTrack(attack)
    suitName = suit.getStyleName()
    if suitName == 'hh':
        leftPosPoints = [
         Point3(0.3, 4.3, 5.3), MovieUtil.PNT3_ZERO]
        rightPosPoints = [Point3(-0.3, 4.3, 5.3), MovieUtil.PNT3_ZERO]
    else:
        if suitName == 'tbc':
            leftPosPoints = [
             Point3(0.6, 4.5, 6), MovieUtil.PNT3_ZERO]
            rightPosPoints = [Point3(-0.6, 4.5, 6), MovieUtil.PNT3_ZERO]
        else:
            leftPosPoints = [
             Point3(0.4, 3.8, 3.7), MovieUtil.PNT3_ZERO]
            rightPosPoints = [Point3(-0.4, 3.8, 3.7), MovieUtil.PNT3_ZERO]
    leftKnifeTracks = Parallel()
    rightKnifeTracks = Parallel()
    for i in range(0, 3):
        knifeDelay = 0.11
        leftTrack = Sequence()
        leftTrack.append(Wait(1.1))
        leftTrack.append(Wait(i * knifeDelay))
        leftTrack.append(getPropAppearTrack(leftKnives[i], suit, leftPosPoints, 1e-06, Point3(0.4, 0.4, 0.4), scaleUpTime=0.1))
        leftTrack.append(getPropThrowTrack(attack, leftKnives[i], hitPointNames=['face'], missPointNames=['miss'], hitDuration=0.3, missDuration=0.3))
        leftKnifeTracks.append(leftTrack)
        rightTrack = Sequence()
        rightTrack.append(Wait(1.1))
        rightTrack.append(Wait(i * knifeDelay))
        rightTrack.append(getPropAppearTrack(rightKnives[i], suit, rightPosPoints, 1e-06, Point3(0.4, 0.4, 0.4), scaleUpTime=0.1))
        rightTrack.append(getPropThrowTrack(attack, rightKnives[i], hitPointNames=['face'], missPointNames=['miss'], hitDuration=0.3, missDuration=0.3))
        rightKnifeTracks.append(rightTrack)

    damageAnims = [['slip-backward', 0.01, 0.35]]
    toonTrack = getToonTrack(attack, damageDelay=1.6, splicedDamageAnims=damageAnims, dodgeDelay=0.7, dodgeAnimNames=['sidestep'])
    soundTrack = getSoundTrack('SA_glower_power.ogg', delay=1.1, node=suit)
    return Parallel(suitTrack, toonTrack, soundTrack, leftKnifeTracks, rightKnifeTracks)


def doHalfWindsor(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    tie = globalPropPool.getProp('half-windsor')
    throwDelay = 2.17
    damageDelay = 3.4
    dodgeDelay = 2.4
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(0.02, 0.88, 0.48), VBase3(99, -3, -108.2)]
    tiePropTrack = getPropAppearTrack(tie, suit.getRightHand(), posPoints, 0.5, Point3(7, 7, 7), scaleUpTime=0.5)
    tiePropTrack.append(Wait(throwDelay))
    missPoint = __toonMissBehindPoint(toon, parent=battle)
    missPoint.setX(missPoint.getX() - 1.1)
    missPoint.setZ(missPoint.getZ() + 4)
    hitPoint = __toonFacePoint(toon, parent=battle)
    hitPoint.setX(hitPoint.getX() - 1.1)
    hitPoint.setY(hitPoint.getY() - 0.7)
    hitPoint.setZ(hitPoint.getZ() + 0.9)
    tiePropTrack.append(getPropThrowTrack(attack, tie, [hitPoint], [missPoint], hitDuration=0.4, missDuration=0.8, missScaleDown=0.3, parent=battle))
    damageAnims = [
     ['conked',
      0.01,
      0.01,
      0.4], ['cringe', 0.01, 0.7]]
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, dodgeAnimNames=['sidestep'])
    throwSound = getSoundTrack('SA_powertie_throw.ogg', delay=throwDelay + 1, node=suit)
    return Parallel(suitTrack, toonTrack, tiePropTrack, throwSound)


def doHeadShrink(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    damageDelay = 2.1
    dodgeDelay = 1.4
    shrinkSpray = BattleParticles.createParticleEffect(file='headShrinkSpray')
    shrinkCloud = BattleParticles.createParticleEffect(file='headShrinkCloud')
    shrinkDrop = BattleParticles.createParticleEffect(file='headShrinkDrop')
    suitTrack = getSuitTrack(attack)
    sprayTrack = getPartTrack(shrinkSpray, 0.3, 1.4, [shrinkSpray, suit, 0])
    shrinkCloud.reparentTo(battle)
    adjust = 0.4
    x = toon.getX(battle)
    y = toon.getY(battle) - adjust
    z = 8
    shrinkCloud.setPos(Point3(x, y, z))
    shrinkDrop.setPos(Point3(0, 0 - adjust, 7.5))
    off = 0.7
    cloudPoints = [Point3(x + off, y, z),
     Point3(x + off / 2, y + off / 2, z),
     Point3(x, y + off, z),
     Point3(x - off / 2, y + off / 2, z),
     Point3(x - off, y, z),
     Point3(x - off / 2, y - off / 2, z),
     Point3(x, y - off, z),
     Point3(x + off / 2, y - off / 2, z),
     Point3(x + off, y, z),
     Point3(x, y, z)]
    circleTrack = Sequence()
    for point in cloudPoints:
        circleTrack.append(LerpPosInterval(shrinkCloud, 0.14, point, other=battle))

    cloudTrack = Sequence()
    cloudTrack.append(Wait(1.42))
    cloudTrack.append(Func(battle.movie.needRestoreParticleEffect, shrinkCloud))
    cloudTrack.append(Func(shrinkCloud.start, battle))
    cloudTrack.append(circleTrack)
    cloudTrack.append(circleTrack)
    cloudTrack.append(LerpFunctionInterval(shrinkCloud.setAlphaScale, fromData=1, toData=0, duration=0.7))
    cloudTrack.append(Func(shrinkCloud.cleanup))
    cloudTrack.append(Func(battle.movie.clearRestoreParticleEffect, shrinkCloud))
    shrinkDelay = 0.8
    shrinkDuration = 1.1
    shrinkTrack = Sequence()
    if dmg > 0:
        headParts = toon.getHeadParts()
        initialScale = headParts.getPath(0).getScale()[0]
        shrinkTrack.append(Wait(damageDelay + shrinkDelay))

        def scaleHeadParallel(scale, duration, headParts=headParts):
            headTracks = Parallel()
            for partNum in range(0, headParts.getNumPaths()):
                nextPart = headParts.getPath(partNum)
                headTracks.append(LerpScaleInterval(nextPart, duration, Point3(scale, scale, scale)))

            return headTracks

        shrinkTrack.append(Func(battle.movie.needRestoreHeadScale))
        shrinkTrack.append(scaleHeadParallel(0.6, shrinkDuration))
        shrinkTrack.append(Wait(1.6))
        shrinkTrack.append(scaleHeadParallel(initialScale * 3.2, 0.4))
        shrinkTrack.append(scaleHeadParallel(initialScale * 0.7, 0.4))
        shrinkTrack.append(scaleHeadParallel(initialScale * 2.5, 0.3))
        shrinkTrack.append(scaleHeadParallel(initialScale * 0.8, 0.3))
        shrinkTrack.append(scaleHeadParallel(initialScale * 1.9, 0.2))
        shrinkTrack.append(scaleHeadParallel(initialScale * 0.85, 0.2))
        shrinkTrack.append(scaleHeadParallel(initialScale * 1.7, 0.15))
        shrinkTrack.append(scaleHeadParallel(initialScale * 0.9, 0.15))
        shrinkTrack.append(scaleHeadParallel(initialScale * 1.3, 0.1))
        shrinkTrack.append(scaleHeadParallel(initialScale, 0.1))
        shrinkTrack.append(Func(battle.movie.clearRestoreHeadScale))
        shrinkTrack.append(Wait(0.7))
    dropTrack = getPartTrack(shrinkDrop, 1.5, 2.5, [shrinkDrop, toon, 0])
    damageAnims = []
    damageAnims.append(['cringe',
     0.01,
     0.65,
     0.2])
    damageAnims.extend(getSplicedLerpAnims('cringe', 0.64, 1.0, startTime=0.85))
    damageAnims.append(['cringe', 0.4, 1.49])
    damageAnims.append(['conked',
     0.01,
     3.6,
     -1.6])
    damageAnims.append(['conked',
     0.01,
     3.1,
     0.4])
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, dodgeAnimNames=['sidestep'])
    if dmg > 0:
        shrinkSound = globalBattleSoundCache.getSound('SA_head_shrink_only.ogg')
        growSound = globalBattleSoundCache.getSound('SA_head_grow_back_only.ogg')
        soundTrack = Sequence(Wait(2.1), SoundInterval(shrinkSound, duration=2.1, node=suit), Wait(1.6), SoundInterval(growSound, node=suit))
        return Parallel(suitTrack, sprayTrack, cloudTrack, dropTrack, toonTrack, shrinkTrack, soundTrack)
    return Parallel(suitTrack, sprayTrack, cloudTrack, dropTrack, toonTrack)


def doRolodex(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    rollodex = globalPropPool.getProp('rollodex')
    particleEffect2 = BattleParticles.createParticleEffect(file='rollodexWaterfall')
    particleEffect3 = BattleParticles.createParticleEffect(file='rollodexStream')
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        propPosPoints = [
         Point3(-0.51, -0.03, -0.1), VBase3(89.673, 2.166, 177.786)]
        propScale = Point3(1.2, 1.2, 1.2)
        partDelay = 2.6
        part2Delay = 2.8
        part3Delay = 3.2
        partDuration = 1.6
        part2Duration = 1.9
        part3Duration = 1
        damageDelay = 3.8
        dodgeDelay = 2.5
    else:
        if suitType == 'b':
            propPosPoints = [
             Point3(0.12, 0.24, 0.01), VBase3(99.032, 5.973, -179.839)]
            propScale = Point3(0.91, 0.91, 0.91)
            partDelay = 2.9
            part2Delay = 3.1
            part3Delay = 3.5
            partDuration = 1.6
            part2Duration = 1.9
            part3Duration = 1
            damageDelay = 4
            dodgeDelay = 2.5
        else:
            if suitType == 'c':
                propPosPoints = [
                 Point3(-0.51, -0.03, -0.1), VBase3(89.673, 2.166, 177.786)]
                propScale = Point3(1.2, 1.2, 1.2)
                partDelay = 2.3
                part2Delay = 2.8
                part3Delay = 3.2
                partDuration = 1.9
                part2Duration = 1.9
                part3Duration = 1
                damageDelay = 3.5
                dodgeDelay = 2.5
    hitPoint = lambda toon=toon: __toonFacePoint(toon)
    partTrack2 = getPartTrack(particleEffect2, part2Delay, part2Duration, [particleEffect2, suit, 0])
    partTrack3 = getPartTrack(particleEffect3, part3Delay, part3Duration, [particleEffect3, suit, 0])
    suitTrack = getSuitTrack(attack)
    propTrack = getPropTrack(rollodex, suit.getLeftHand(), propPosPoints, 1e-06, 4.7, scaleUpPoint=propScale, anim=0, propName='rollodex', animDuration=0, animStartTime=0)
    toonTrack = getToonTrack(attack, damageDelay, ['conked'], dodgeDelay, ['sidestep'])
    soundTrack = getSoundTrack('SA_rolodex.ogg', delay=2.8, node=suit)
    return Parallel(suitTrack, toonTrack, propTrack, soundTrack, partTrack2, partTrack3)


def doEvilEye(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    eye = globalPropPool.getProp('evil-eye')
    damageDelay = 2.44
    dodgeDelay = 1.64
    suitName = suit.getStyleName()
    if suitName == 'cr':
        posPoints = [
         Point3(-0.46, 4.85, 5.28), VBase3(-155.0, -20.0, 0.0)]
    else:
        if suitName == 'tf':
            posPoints = [
             Point3(-0.4, 3.65, 5.01), VBase3(-155.0, -20.0, 0.0)]
        else:
            if suitName == 'le':
                posPoints = [
                 Point3(-0.64, 4.45, 5.91), VBase3(-155.0, -20.0, 0.0)]
            else:
                posPoints = [
                 Point3(-0.4, 3.65, 5.01), VBase3(-155.0, -20.0, 0.0)]
    appearDelay = 0.8
    suitHoldStart = 1.06
    suitHoldStop = 1.69
    suitHoldDuration = suitHoldStop - suitHoldStart
    eyeHoldDuration = 1.1
    moveDuration = 1.1
    suitSplicedAnims = []
    suitSplicedAnims.append(['glower',
     0.01,
     0.01,
     suitHoldStart])
    suitSplicedAnims.extend(getSplicedLerpAnims('glower', suitHoldDuration, 1.1, startTime=suitHoldStart))
    suitSplicedAnims.append(['glower', 0.01, suitHoldStop])
    suitTrack = getSuitTrack(attack, splicedAnims=suitSplicedAnims)
    eyeAppearTrack = Sequence(Wait(suitHoldStart), Func(__showProp, eye, suit, posPoints[0], posPoints[1]), LerpScaleInterval(eye, suitHoldDuration, Point3(11, 11, 11)), Wait(eyeHoldDuration * 0.3), LerpHprInterval(eye, 0.02, Point3(205, 40, 0)), Wait(eyeHoldDuration * 0.7), Func(battle.movie.needRestoreRenderProp, eye), Func(eye.wrtReparentTo, battle))
    toonFace = __toonFacePoint(toon, parent=battle)
    if dmg > 0:
        lerpInterval = LerpPosInterval(eye, moveDuration, toonFace)
    else:
        lerpInterval = LerpPosInterval(eye, moveDuration, Point3(toonFace.getX(), toonFace.getY() - 5, toonFace.getZ() - 2))
    eyeMoveTrack = lerpInterval
    eyeRollTrack = LerpHprInterval(eye, moveDuration, Point3(0, 0, -180))
    eyePropTrack = Sequence(eyeAppearTrack, Parallel(eyeMoveTrack, eyeRollTrack), Func(battle.movie.clearRenderProp, eye), Func(MovieUtil.removeProp, eye))
    damageAnims = [
     ['duck',
      0.01,
      0.01,
      1.4], ['cringe', 0.01, 0.3]]
    toonTrack = getToonTrack(attack, splicedDamageAnims=damageAnims, damageDelay=damageDelay, dodgeDelay=dodgeDelay, dodgeAnimNames=['duck'], showDamageExtraTime=1.7, showMissedExtraTime=1.7)
    soundTrack = getSoundTrack('SA_evil_eye.ogg', delay=1.3, node=suit)
    return Parallel(suitTrack, toonTrack, eyePropTrack, soundTrack)


def doPierce(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    eye = globalPropPool.getProp('dagger')
    damageDelay = 2.44
    dodgeDelay = 1.64
    suitName = suit.getStyleName()
    posPoints = [Point3(-0.4, 3.65, 4.01), VBase3(-155.0, -20.0, 0.0)]
    appearDelay = 0.8
    suitHoldStart = 1.06
    suitHoldStop = 1.69
    suitHoldDuration = suitHoldStop - suitHoldStart
    eyeHoldDuration = 1.1
    moveDuration = 1.1
    suitSplicedAnims = []
    suitSplicedAnims.append(['glower',
     0.01,
     0.01,
     suitHoldStart])
    suitSplicedAnims.extend(getSplicedLerpAnims('glower', suitHoldDuration, 1.1, startTime=suitHoldStart))
    suitSplicedAnims.append(['glower', 0.01, suitHoldStop])
    suitTrack = getSuitTrack(attack, splicedAnims=suitSplicedAnims)
    eyeAppearTrack = Sequence(LerpScaleInterval(eye, 0, Point3(0.01, 0.01, 0.01)), Wait(suitHoldStart), Func(__showProp, eye, suit, posPoints[0], posPoints[1]), LerpScaleInterval(eye, suitHoldDuration, Point3(1, 1, 1)), Wait(eyeHoldDuration * 0.3), LerpHprInterval(eye, 0.02, Point3(-155, 180, 0)), Wait(eyeHoldDuration * 0.7), Func(battle.movie.needRestoreRenderProp, eye), Func(eye.wrtReparentTo, battle))
    toonFace = __toonFacePoint(toon, parent=battle)
    if dmg > 0:
        lerpInterval = LerpPosInterval(eye, moveDuration, toonFace)
    else:
        lerpInterval = LerpPosInterval(eye, moveDuration, Point3(toonFace.getX(), toonFace.getY() - 5, toonFace.getZ() - 2))
    eyeMoveTrack = lerpInterval
    eyePropTrack = Sequence(eyeAppearTrack, Parallel(eyeMoveTrack), Func(battle.movie.clearRenderProp, eye), Func(MovieUtil.removeProp, eye))
    damageAnims = [
     ['duck',
      0.01,
      0.01,
      1.4], ['cringe', 0.01, 0.3]]
    toonTrack = getToonTrack(attack, splicedDamageAnims=damageAnims, damageDelay=damageDelay, dodgeDelay=dodgeDelay, dodgeAnimNames=['duck'], showDamageExtraTime=1.7, showMissedExtraTime=1.7)
    soundTrack = getSoundTrack('SA_evil_eye.ogg', delay=1.3, node=suit)
    return Parallel(suitTrack, toonTrack, eyePropTrack, soundTrack)


def doPlayHardball(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    ball = globalPropPool.getProp('baseball')
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        suitDelay = 1.09
        damageDelay = 2.76
        dodgeDelay = 1.86
    else:
        if suitType == 'b':
            suitDelay = 1.79
            damageDelay = 3.46
            dodgeDelay = 2.56
        else:
            if suitType == 'c':
                suitDelay = 1.09
                damageDelay = 2.76
                dodgeDelay = 1.86
    suitTrack = getSuitTrack(attack)
    ballPosPoints = [Point3(0.04, 0.03, -0.31), VBase3(-1.152, 86.581, -76.784)]
    propTrack = Sequence(getPropAppearTrack(ball, suit.getRightHand(), ballPosPoints, 0.8, Point3(5, 5, 5), scaleUpTime=0.5))
    propTrack.append(Wait(suitDelay))
    propTrack.append(Func(battle.movie.needRestoreRenderProp, ball))
    propTrack.append(Func(ball.wrtReparentTo, battle))
    toonPos = toon.getPos(battle)
    x = toonPos.getX()
    y = toonPos.getY()
    z = toonPos.getZ()
    z = z + 0.2
    if dmg > 0:
        propTrack.append(LerpPosInterval(ball, 0.5, __toonFacePoint(toon, parent=battle)))
        propTrack.append(LerpPosInterval(ball, 0.5, Point3(x, y + 3, z)))
        propTrack.append(LerpPosInterval(ball, 0.4, Point3(x, y + 5, z + 2)))
        propTrack.append(LerpPosInterval(ball, 0.3, Point3(x, y + 6, z)))
        propTrack.append(LerpPosInterval(ball, 0.1, Point3(x, y + 7, z + 1)))
        propTrack.append(LerpPosInterval(ball, 0.1, Point3(x, y + 8, z)))
        propTrack.append(LerpPosInterval(ball, 0.1, Point3(x, y + 8.5, z + 0.6)))
        propTrack.append(LerpPosInterval(ball, 0.1, Point3(x, y + 9, z + 0.2)))
        propTrack.append(Wait(0.4))
        soundTrack = getSoundTrack('SA_hardball_impact_only.ogg', delay=2.8, node=suit)
    else:
        propTrack.append(LerpPosInterval(ball, 0.5, Point3(x, y + 2, z)))
        propTrack.append(LerpPosInterval(ball, 0.4, Point3(x, y - 1, z + 2)))
        propTrack.append(LerpPosInterval(ball, 0.3, Point3(x, y - 3, z)))
        propTrack.append(LerpPosInterval(ball, 0.1, Point3(x, y - 4, z + 1)))
        propTrack.append(LerpPosInterval(ball, 0.1, Point3(x, y - 5, z)))
        propTrack.append(LerpPosInterval(ball, 0.1, Point3(x, y - 5.5, z + 0.6)))
        propTrack.append(LerpPosInterval(ball, 0.1, Point3(x, y - 6, z + 0.2)))
        propTrack.append(Wait(0.4))
        soundTrack = getSoundTrack('SA_hardball.ogg', delay=3.1, node=suit)
    propTrack.append(LerpScaleInterval(ball, 0.3, MovieUtil.PNT3_NEARZERO))
    propTrack.append(Func(MovieUtil.removeProp, ball))
    propTrack.append(Func(battle.movie.clearRenderProp, ball))
    damageAnims = [
     ['conked',
      damageDelay,
      0.01,
      0.5], ['slip-backward', 0.01, 0.7]]
    toonTrack = getToonTrack(attack, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, dodgeAnimNames=['sidestep'], showDamageExtraTime=3.9)
    return Parallel(suitTrack, toonTrack, propTrack, soundTrack)


def doPowerTie(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    tie = globalPropPool.getProp('power-tie')
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        throwDelay = 2.17
        damageDelay = 3.3
        dodgeDelay = 3.1
    else:
        if suitType == 'b':
            throwDelay = 2.17
            damageDelay = 3.3
            dodgeDelay = 3.1
        else:
            if suitType == 'c':
                throwDelay = 1.45
                damageDelay = 2.61
                dodgeDelay = 2.34
        suitTrack = getSuitTrack(attack)
        posPoints = [Point3(1.16, 0.24, 0.63), VBase3(171.561, 1.745, -163.443)]
        tiePropTrack = Sequence(getPropAppearTrack(tie, suit.getRightHand(), posPoints, 0.5, Point3(3.5, 3.5, 3.5), scaleUpTime=0.5))
        tiePropTrack.append(Wait(throwDelay))
        tiePropTrack.append(Func(tie.setBillboardPointEye))
        tiePropTrack.append(getPropThrowTrack(attack, tie, [__toonFacePoint(toon)], [__toonGroundPoint(attack, toon, 0.1)], hitDuration=0.4, missDuration=0.8))
        toonTrack = getToonTrack(attack, damageDelay, ['conked'], dodgeDelay, ['sidestep'])
        throwSound = getSoundTrack('SA_powertie_throw.ogg', delay=2.3, node=suit)
        if dmg > 0:
            hitSound = getSoundTrack('SA_powertie_impact.ogg', delay=2.9, node=suit)
            return Parallel(suitTrack, toonTrack, tiePropTrack, throwSound, hitSound)
    return Parallel(suitTrack, toonTrack, tiePropTrack, throwSound)


def doDoubleTalk(attack):
    suit = attack['suit']
    battle = attack['battle']
    BattleParticles.loadParticles()
    particleEffect = BattleParticles.createParticleEffect('DoubleTalkLeft')
    particleEffect2 = BattleParticles.createParticleEffect('DoubleTalkRight')
    BattleParticles.setEffectTexture(particleEffect, 'doubletalk-double', color=Vec4(0, 1.0, 0.0, 1))
    BattleParticles.setEffectTexture(particleEffect2, 'doubletalk-good', color=Vec4(0, 1.0, 0.0, 1))
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        partDelay = 3.3
        damageDelay = 3.5
        dodgeDelay = 3.3
    else:
        if suitType == 'b':
            partDelay = 3.3
            damageDelay = 3.5
            dodgeDelay = 3.3
        else:
            if suitType == 'c':
                partDelay = 3.3
                damageDelay = 3.5
                dodgeDelay = 3.3
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(particleEffect, partDelay, 1.8, [particleEffect, suit, 0])
    partTrack2 = getPartTrack(particleEffect2, partDelay, 1.8, [particleEffect2, suit, 0])
    damageAnims = [
     ['duck',
      0.01,
      0.4,
      1.05], ['cringe', 1e-06, 0.8]]
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, splicedDodgeAnims=[['duck', 0.01, 1.4]], showMissedExtraTime=0.9, showDamageExtraTime=0.8)
    soundTrack = getSoundTrack('SA_filibuster.ogg', delay=2.5, node=suit)
    return Parallel(suitTrack, toonTrack, partTrack, partTrack2, soundTrack)


def doShadowToon(attack):
    suit = attack['suit']
    toon = attack['target']['toon']
    hp = attack['target']['hp']
    battle = attack['battle']
    tauntIndex = attack['taunt']
    taunt = getAttackTaunt(attack['name'], tauntIndex)
    oldPos = suit.getPos(battle)
    oldHpr = suit.getHpr(battle)
    toonPos = toon.getPos(battle)
    newPos = oldPos + Point3(0, 5, 0)
    tPieLeavesHand = 2.7
    tPieHitsSuit = 3.0
    tSuitDodges = 2.45
    ratioMissToHit = 1.5

    def createEvilToon(toon=toon, oldPos=oldPos):
        evilToon = Toon.Toon()
        style = toon.style.clone()
        evilToon.setDNA(style)
        evilToon.hat = toon.getHat()
        evilToon.glasses = toon.getGlasses()
        evilToon.backpack = toon.getBackpack()
        evilToon.shoes = toon.getShoes()
        evilToon.generateToonAccessories()
        evilToon.setColorScale(0, 0, 0, 1)
        evilToon.setPos(battle, oldPos)
        evilToon.setHpr(battle, oldHpr)
        return evilToon

    evilToon = createEvilToon()
    evilToon.loop('neutral')

    def getDustCloudIval(evilToon=evilToon, oldPos=oldPos):
        dustCloud = DustCloud.DustCloud(fBillboard=0, wantSound=1)
        dustCloud.setBillboardAxis(2.0)
        dustCloud.setZ(3)
        dustCloud.setScale(0.4)
        dustCloud.createTrack()
        dustCloud.setColorScale(0.2, 0.2, 0.2, 1)
        return Sequence(Func(dustCloud.reparentTo, render), Func(dustCloud.setPos, battle, oldPos + (0, 0, evilToon.getHeight())), dustCloud.track, Func(dustCloud.destroy), name='dustCloadIval')

    suitTrack = Sequence(Parallel(LerpPosInterval(suit, duration=1.0, pos=newPos, other=battle), ActorInterval(suit, 'walk', loop=1, playRate=-1, duration=1.0)), Parallel(Sequence(Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), ActorInterval(suit, 'magic2'), Func(suit.loop, 'neutral')), Sequence(Wait(1.35), Func(getDustCloudIval().start), Wait(0.5), Func(evilToon.addActive), Func(evilToon.reparentTo, render))))
    pieName = 'creampie'
    pie = globalPropPool.getProp(pieName)
    pieType = globalPropPool.getPropType(pieName)
    pie2 = MovieUtil.copyProp(pie)
    pies = [pie, pie2]
    for p in pies:
        p.setColorScale(0, 0, 0, 1)

    hands = evilToon.getRightHands()
    splatName = 'splat-' + pieName
    splat = globalPropPool.getProp(splatName)
    splatType = globalPropPool.getPropType(splatName)
    splat.setColorScale(0, 0, 0, 1)
    evilToonTrack = Sequence()
    toonFace = Func(evilToon.headsUp, battle, toonPos)
    evilToonTrack.append(toonFace)
    evilToonTrack.append(ActorInterval(evilToon, 'throw'))
    evilToonTrack.append(Func(evilToon.loop, 'neutral'))
    evilToonTrack.append(Func(getDustCloudIval().start))
    evilToonTrack.append(Wait(0.5))
    evilToonTrack.append(Func(evilToon.reparentTo, hidden))
    evilToonTrack.append(Sequence(Func(evilToon.removeActive), Func(evilToon.cleanup), Func(evilToon.removeNode)))
    hitToon = hp > 0
    pieShow = Func(MovieUtil.showProps, pies, hands)
    pieAnim = Func(__animProp, pies, pieName, pieType)
    pieScale1 = LerpScaleInterval(pie, 1.0, pie.getScale(), startScale=MovieUtil.PNT3_NEARZERO)
    pieScale2 = LerpScaleInterval(pie2, 1.0, pie2.getScale(), startScale=MovieUtil.PNT3_NEARZERO)
    pieScale = Parallel(pieScale1, pieScale2)
    piePreflight = Func(__propPreflight, pies, toon, evilToon, battle)
    pieTrack = Sequence(pieShow, pieAnim, pieScale, Func(battle.movie.needRestoreRenderProp, pies[0]), Wait(tPieLeavesHand - 1.0), piePreflight)
    soundTrack = __getSoundTrack(0, hitToon, tPieLeavesHand, evilToon)
    if hitToon:
        pieFly = LerpPosInterval(pie, tPieHitsSuit - tPieLeavesHand, pos=MovieUtil.avatarFacePoint(toon, other=battle), other=battle)
        pieHide = Func(MovieUtil.removeProps, pies)
        splatShow = Func(__showProp, splat, toon, Point3(0, 0, toon.getHeight()))
        splatBillboard = Func(__billboardProp, splat)
        splatAnim = ActorInterval(splat, splatName)
        splatHide = Func(MovieUtil.removeProp, splat)
        pieTrack.append(pieFly)
        pieTrack.append(pieHide)
        pieTrack.append(Func(battle.movie.clearRenderProp, pies[0]))
        pieTrack.append(splatShow)
        pieTrack.append(splatBillboard)
        pieTrack.append(splatAnim)
        pieTrack.append(splatHide)
    else:
        missDict = {}
        suitPoint = __suitMissPoint(toon, other=battle)
        piePreMiss = Func(__piePreMiss, missDict, pie, suitPoint, battle)
        pieMiss = LerpFunctionInterval(__pieMissLerpCallback, extraArgs=[missDict], duration=(tPieHitsSuit - tPieLeavesHand) * ratioMissToHit)
        pieHide = Func(MovieUtil.removeProps, pies)
        pieTrack.append(piePreMiss)
        pieTrack.append(pieMiss)
        pieTrack.append(pieHide)
        pieTrack.append(Func(battle.movie.clearRenderProp, pies[0]))
    moveUp = Sequence(Parallel(LerpPosInterval(suit, duration=1.0, pos=oldPos, other=battle), ActorInterval(suit, 'walk', loop=1, duration=1.0)), Func(suit.loop, 'neutral'))
    if toon.isDisguised:
        toonTrack = getToonTrack(attack, tPieHitsSuit, ['cringe'], tSuitDodges, ['sidestep'])
    else:
        toonTrack = getToonTrack(attack, tPieHitsSuit, ['slip-backward'], tSuitDodges, ['sidestep'])
    return Sequence(suitTrack, Parallel(evilToonTrack, pieTrack, soundTrack, toonTrack), moveUp)


def doFreezeAssets(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    BattleParticles.loadParticles()
    snowEffect = BattleParticles.createParticleEffect('FreezeAssets')
    BattleParticles.setEffectTexture(snowEffect, 'snow-particle')
    cloud = globalPropPool.getProp('stormcloud')
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        partDelay = 0.2
        damageDelay = 3.5
        dodgeDelay = 2.3
    else:
        if suitType == 'b':
            partDelay = 0.2
            damageDelay = 3.5
            dodgeDelay = 2.3
        else:
            if suitType == 'c':
                partDelay = 0.2
                damageDelay = 3.5
                dodgeDelay = 2.3
    suitTrack = getSuitTrack(attack, delay=0.9)
    initialCloudHeight = suit.height + 3
    cloudPosPoints = [Point3(0, 3, initialCloudHeight), MovieUtil.PNT3_ZERO]
    cloudPropTrack = Sequence()
    cloudPropTrack.append(Func(cloud.pose, 'stormcloud', 0))
    cloudPropTrack.append(getPropAppearTrack(cloud, suit, cloudPosPoints, 1e-06, Point3(3, 3, 3), scaleUpTime=0.7))
    cloudPropTrack.append(Func(battle.movie.needRestoreRenderProp, cloud))
    cloudPropTrack.append(Func(cloud.wrtReparentTo, render))
    targetPoint = __toonFacePoint(toon)
    targetPoint.setZ(targetPoint[2] + 3)
    cloudPropTrack.append(Wait(1.1))
    cloudPropTrack.append(LerpPosInterval(cloud, 1, pos=targetPoint))
    cloudPropTrack.append(Wait(partDelay))
    cloudPropTrack.append(ParticleInterval(snowEffect, cloud, worldRelative=0, duration=2.1, cleanup=True))
    cloudPropTrack.append(Wait(0.4))
    cloudPropTrack.append(LerpScaleInterval(cloud, 0.5, MovieUtil.PNT3_NEARZERO))
    cloudPropTrack.append(Func(MovieUtil.removeProp, cloud))
    cloudPropTrack.append(Func(battle.movie.clearRenderProp, cloud))
    damageAnims = [
     ['cringe',
      0.01,
      0.4,
      0.8], ['duck', 0.01, 1.6]]
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, dodgeAnimNames=['sidestep'], showMissedExtraTime=1.2)
    return Parallel(suitTrack, toonTrack, cloudPropTrack)


def doHotAir(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    BattleParticles.loadParticles()
    sprayEffect = BattleParticles.createParticleEffect('HotAir')
    baseFlameEffect = BattleParticles.createParticleEffect(file='firedBaseFlame')
    flameEffect = BattleParticles.createParticleEffect('FiredFlame')
    flecksEffect = BattleParticles.createParticleEffect('SpriteFiredFlecks')
    BattleParticles.setEffectTexture(sprayEffect, 'fire')
    BattleParticles.setEffectTexture(baseFlameEffect, 'fire')
    BattleParticles.setEffectTexture(flameEffect, 'fire')
    BattleParticles.setEffectTexture(flecksEffect, 'roll-o-dex', color=Vec4(0.95, 0.95, 0.0, 1))
    sprayDelay = 1.3
    flameDelay = 3.2
    flameDuration = 2.6
    flecksDelay = flameDelay + 0.8
    flecksDuration = flameDuration - 0.8
    damageDelay = 3.6
    dodgeDelay = 2.0
    suitTrack = getSuitTrack(attack)
    sprayTrack = getPartTrack(sprayEffect, sprayDelay, 2.3, [sprayEffect, suit, 0])
    baseFlameTrack = getPartTrack(baseFlameEffect, flameDelay, flameDuration, [baseFlameEffect, toon, 0])
    flameTrack = getPartTrack(flameEffect, flameDelay, flameDuration, [flameEffect, toon, 0])
    flecksTrack = getPartTrack(flecksEffect, flecksDelay, flecksDuration, [flecksEffect, toon, 0])

    def changeColor(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(Func(nextPart.setColorScale, Vec4(0, 0, 0, 1)))

        return track

    def resetColor(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(Func(nextPart.clearColorScale))

        return track

    if dmg > 0:
        headParts = toon.getHeadParts()
        torsoParts = toon.getTorsoParts()
        legsParts = toon.getLegsParts()
        colorTrack = Sequence()
        colorTrack.append(Wait(4.0))
        colorTrack.append(Func(battle.movie.needRestoreColor))
        colorTrack.append(changeColor(headParts))
        colorTrack.append(changeColor(torsoParts))
        colorTrack.append(changeColor(legsParts))
        colorTrack.append(Wait(3.5))
        colorTrack.append(resetColor(headParts))
        colorTrack.append(resetColor(torsoParts))
        colorTrack.append(resetColor(legsParts))
        colorTrack.append(Func(battle.movie.clearRestoreColor))
    damageAnims = []
    damageAnims.append(['cringe',
     0.01,
     0.7,
     0.62])
    damageAnims.append(['slip-forward',
     0.01,
     0.4,
     1.2])
    damageAnims.append(['slip-forward', 0.01, 1.0])
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, dodgeAnimNames=['sidestep'])
    soundTrack = getSoundTrack('SA_hot_air.ogg', delay=1.6, node=suit)
    if dmg > 0:
        return Parallel(suitTrack, toonTrack, sprayTrack, soundTrack, baseFlameTrack, flameTrack, flecksTrack, colorTrack)
    return Parallel(suitTrack, toonTrack, sprayTrack, soundTrack)


def doPickPocket(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    dmg = target['hp']
    bill = globalPropPool.getProp('1dollar')
    suitTrack = getSuitTrack(attack)
    billPosPoints = [Point3(-0.01, 0.45, -0.25), VBase3(136.424, -46.434, -129.712)]
    billPropTrack = getPropTrack(bill, suit.getRightHand(), billPosPoints, 0.6, 0.55, scaleUpPoint=Point3(1.41, 1.41, 1.41))
    toonTrack = getToonTrack(attack, 0.6, ['cringe'], 0.01, ['sidestep'])
    multiTrackList = Parallel(suitTrack, toonTrack)
    if dmg > 0:
        soundTrack = getSoundTrack('SA_pick_pocket.ogg', delay=0.2, node=suit)
        multiTrackList.append(billPropTrack)
        multiTrackList.append(soundTrack)
    return multiTrackList


def doFilibuster(attack):
    suit = attack['suit']
    target = attack['target']
    dmg = target['hp']
    battle = attack['battle']
    BattleParticles.loadParticles()
    sprayEffect = BattleParticles.createParticleEffect(file='filibusterSpray')
    sprayEffect2 = BattleParticles.createParticleEffect(file='filibusterSpray')
    sprayEffect3 = BattleParticles.createParticleEffect(file='filibusterSpray')
    sprayEffect4 = BattleParticles.createParticleEffect(file='filibusterSpray')
    color = Vec4(0.4, 0, 0, 1)
    BattleParticles.setEffectTexture(sprayEffect, 'filibuster-cut', color=color)
    BattleParticles.setEffectTexture(sprayEffect2, 'filibuster-fiscal', color=color)
    BattleParticles.setEffectTexture(sprayEffect3, 'filibuster-impeach', color=color)
    BattleParticles.setEffectTexture(sprayEffect4, 'filibuster-inc', color=color)
    partDelay = 1.3
    partDuration = 1.15
    damageDelay = 2.45
    dodgeDelay = 1.7
    suitTrack = getSuitTrack(attack)
    sprayTrack = getPartTrack(sprayEffect, partDelay, partDuration, [sprayEffect, suit, 0])
    sprayTrack2 = getPartTrack(sprayEffect2, partDelay + 0.8, partDuration, [sprayEffect2, suit, 0])
    sprayTrack3 = getPartTrack(sprayEffect3, partDelay + 1.6, partDuration, [sprayEffect3, suit, 0])
    sprayTrack4 = getPartTrack(sprayEffect4, partDelay + 2.4, partDuration, [sprayEffect4, suit, 0])
    damageAnims = []
    for i in range(0, 4):
        damageAnims.append(['cringe',
         1e-05,
         0.3,
         0.8])

    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, dodgeAnimNames=['sidestep'])
    soundTrack = getSoundTrack('SA_filibuster.ogg', delay=1.1, node=suit)
    if dmg > 0:
        return Parallel(suitTrack, toonTrack, soundTrack, sprayTrack, sprayTrack2, sprayTrack3, sprayTrack4)
    return Parallel(suitTrack, toonTrack, soundTrack, sprayTrack, sprayTrack2, sprayTrack3)


def doSchmooze(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    dmg = target['hp']
    BattleParticles.loadParticles()
    upperEffects = []
    lowerEffects = []
    textureNames = ['schmooze-genius',
     'schmooze-instant',
     'schmooze-master',
     'schmooze-viz']
    for i in range(0, 4):
        upperEffect = BattleParticles.createParticleEffect(file='schmoozeUpperSpray')
        lowerEffect = BattleParticles.createParticleEffect(file='schmoozeLowerSpray')
        BattleParticles.setEffectTexture(upperEffect, textureNames[i], color=Vec4(0, 0, 1, 1))
        BattleParticles.setEffectTexture(lowerEffect, textureNames[i], color=Vec4(0, 0, 1, 1))
        upperEffects.append(upperEffect)
        lowerEffects.append(lowerEffect)

    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        partDelay = 1.3
        damageDelay = 1.8
        dodgeDelay = 1.1
    else:
        if suitType == 'b':
            partDelay = 1.3
            damageDelay = 2.5
            dodgeDelay = 1.8
        else:
            if suitType == 'c':
                partDelay = 1.3
                damageDelay = partDelay + 1.4
                dodgeDelay = 0.9
        suitTrack = getSuitTrack(attack)
        upperPartTracks = Parallel()
        lowerPartTracks = Parallel()
        for i in range(0, 4):
            upperPartTracks.append(getPartTrack(upperEffects[i], partDelay + i * 0.65, 0.8, [upperEffects[i], suit, 0]))
            lowerPartTracks.append(getPartTrack(lowerEffects[i], partDelay + i * 0.65 + 0.7, 1.0, [lowerEffects[i], suit, 0]))

        damageAnims = []
        for i in range(0, 3):
            damageAnims.append(['conked',
             0.01,
             0.3,
             0.71])

        damageAnims.append(['conked', 0.01, 0.3])
        dodgeAnims = []
        dodgeAnims.append(['duck',
         0.01,
         0.2,
         2.7])
        dodgeAnims.append(['duck',
         0.01,
         1.22,
         1.28])
        dodgeAnims.append(['duck', 0.01, 3.16])
        toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, splicedDodgeAnims=dodgeAnims, showMissedExtraTime=1.9, showDamageExtraTime=1.1)
        if dmg > 0:
            hitSound = getSoundTrack('SA_schmooze.ogg', delay=damageDelay + 0.35, startTime=1.2, node=suit)
            return Parallel(suitTrack, toonTrack, upperPartTracks, lowerPartTracks, hitSound)
    return Parallel(suitTrack, toonTrack, upperPartTracks, lowerPartTracks)


def doQuake(attack):
    suit = attack['suit']
    suitTrack = getSuitAnimTrack(attack)
    damageAnims = [['slip-forward'], ['slip-forward', 0.01]]
    dodgeAnims = [['jump'], ['jump', 0.01], ['jump', 0.01]]
    toonTracks = getToonTracks(attack, damageDelay=1.8, splicedDamageAnims=damageAnims, dodgeDelay=1.1, splicedDodgeAnims=dodgeAnims, showMissedExtraTime=2.8, showDamageExtraTime=1.1)
    return Parallel(suitTrack, toonTracks)


def doShake(attack):
    suit = attack['suit']
    suitTrack = getSuitAnimTrack(attack)
    damageAnims = [['slip-forward'], ['slip-forward', 0.01]]
    dodgeAnims = [['jump'], ['jump', 0.01]]
    toonTracks = getToonTracks(attack, damageDelay=1.1, splicedDamageAnims=damageAnims, dodgeDelay=0.7, splicedDodgeAnims=dodgeAnims, showMissedExtraTime=2.8, showDamageExtraTime=1.1)
    return Parallel(suitTrack, toonTracks)


def doTremor(attack):
    suit = attack['suit']
    suitTrack = getSuitAnimTrack(attack)
    damageAnims = [['slip-forward'], ['slip-forward', 0.01]]
    dodgeAnims = [['jump'], ['jump', 0.01]]
    toonTracks = getToonTracks(attack, damageDelay=1.1, splicedDamageAnims=damageAnims, dodgeDelay=0.7, splicedDodgeAnims=dodgeAnims, showMissedExtraTime=2.8, showDamageExtraTime=1.1)
    soundTrack = getSoundTrack('SA_tremor.ogg', delay=0.9, node=suit)
    return Parallel(suitTrack, soundTrack, toonTracks)


def doFlex(attack):
    suit = attack['suit']
    suitTrack = getSuitAnimTrack(attack)
    targets = attack['target']
    hitAtleastOneToon = 0
    missedOneToon = 0
    for t in targets:
        if t['hp'] > 0:
            hitAtleastOneToon = 1
        else:
            missedOneToon = 1

    damageAnims = [
     [
      'cringe']]
    dodgeAnims = [['shrug']]
    suitsfx = globalBattleSoundCache.getSound('SA_watercooler_appear_only.ogg')
    toonTracks = getToonTracks(attack, damageDelay=1.8, splicedDamageAnims=damageAnims, dodgeDelay=1.1, splicedDodgeAnims=dodgeAnims, showMissedExtraTime=1.8, showDamageExtraTime=1.1)
    throwSound = Sequence(Wait(0.6), SoundInterval(suitsfx, node=suit, duration=0.4))
    toonsfx = base.loader.loadSfx('phase_3.5/audio/sfx/avatar_emotion_shrug.ogg')
    missSound = Sequence(Wait(1.1), SoundInterval(toonsfx, node=suit))
    hitSound = getSoundTrack('SA_powertie_impact.ogg', delay=1.8, node=suit)
    if hitAtleastOneToon == 1:
        if missedOneToon == 1:
            return Parallel(suitTrack, toonTracks, throwSound, hitSound, missSound)
        return Parallel(suitTrack, toonTracks, throwSound, hitSound)
    else:
        return Parallel(suitTrack, toonTracks, throwSound, missSound)


def doSongAndDance(attack):
    suit = attack['suit']
    suitTrack = getSuitAnimTrack(attack)
    targets = attack['target']
    hitAtleastOneToon = 0
    for t in targets:
        if t['hp'] > 0:
            hitAtleastOneToon = 1

    damageAnims = []
    damageAnims.append(['conked',
     0.01,
     0.52,
     0.6])
    damageAnims.append(['slip-backward',
     0.01,
     0.4])
    dodgeAnims = [['victory']]
    suitsfx = globalBattleSoundCache.getSound('AA_heal_happydance.ogg')
    throwSound = Sequence(SoundInterval(suitsfx, node=suit))
    hitsfx1 = base.loader.loadSfx('phase_4/audio/sfx/avatar_emotion_surprise.ogg')
    hitsfx2 = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_hit_dirt.ogg')
    hitSound1 = Sequence(Wait(1.8), SoundInterval(hitsfx1, node=suit))
    hitSound2 = Sequence(Wait(2.1), SoundInterval(hitsfx2, node=suit))
    toonTracks = getToonTracks(attack, damageDelay=1.8, splicedDamageAnims=damageAnims, dodgeDelay=1.1, splicedDodgeAnims=dodgeAnims, showMissedExtraTime=2.8, showDamageExtraTime=1.1)
    if hitAtleastOneToon == 1:
        return Parallel(suitTrack, toonTracks, throwSound, hitSound1, hitSound2)
    return Parallel(suitTrack, toonTracks, throwSound)


def doHangUp(attack):
    suit = attack['suit']
    battle = attack['battle']
    phone = globalPropPool.getProp('phone')
    receiver = globalPropPool.getProp('receiver')
    suitTrack = getSuitTrack(attack)
    suitName = suit.getStyleName()
    if suitName == 'tf':
        phonePosPoints = [
         Point3(-0.23, 0.01, -0.26), VBase3(5.939, 2.763, -177.591)]
        receiverPosPoints = [Point3(-0.13, -0.07, -0.06), VBase3(-1.854, 2.434, -177.579)]
        receiverAdjustScale = Point3(0.8, 0.8, 0.8)
        pickupDelay = 0.44
        dialDuration = 3.07
        finalPhoneDelay = 0.01
        scaleUpPoint = Point3(0.75, 0.75, 0.75)
    else:
        phonePosPoints = [
         Point3(0.23, 0.17, -0.11), VBase3(5.939, 2.763, -177.591)]
        receiverPosPoints = [Point3(0.23, 0.17, -0.11), VBase3(5.939, 2.763, -177.591)]
        receiverAdjustScale = MovieUtil.PNT3_ONE
        pickupDelay = 0.74
        dialDuration = 3.07
        finalPhoneDelay = 0.69
        scaleUpPoint = MovieUtil.PNT3_ONE
    propTrack = Sequence(Wait(0.3), Func(__showProp, phone, suit.getLeftHand(), phonePosPoints[0], phonePosPoints[1]), Func(__showProp, receiver, suit.getLeftHand(), receiverPosPoints[0], receiverPosPoints[1]), LerpScaleInterval(phone, 0.5, scaleUpPoint, MovieUtil.PNT3_NEARZERO), Wait(pickupDelay), Func(receiver.wrtReparentTo, suit.getRightHand()), LerpScaleInterval(receiver, 0.01, receiverAdjustScale), LerpPosHprInterval(receiver, 0.0001, Point3(-0.53, 0.21, -0.54), VBase3(-99.49, -35.27, 1.84)), Wait(dialDuration), Func(receiver.wrtReparentTo, phone), Wait(finalPhoneDelay), LerpScaleInterval(phone, 0.5, MovieUtil.PNT3_NEARZERO), Func(MovieUtil.removeProps, [receiver, phone]))
    toonTrack = getToonTrack(attack, 5.5, ['slip-backward'], 4.7, ['jump'])
    soundTrack = getSoundTrack('SA_hangup.ogg', delay=1.3, node=suit)
    return Parallel(suitTrack, toonTrack, propTrack, soundTrack)


def doRedTape(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    tape = globalPropPool.getProp('redtape')
    tubes = []
    for i in range(0, 3):
        tubes.append(globalPropPool.getProp('redtape-tube'))

    suitTrack = getSuitTrack(attack)
    suitName = suit.getStyleName()
    if suitName == 'tf' or suitName == 'nc':
        tapePosPoints = [
         Point3(-0.24, 0.09, -0.38), VBase3(-1.152, 86.581, -76.784)]
    else:
        tapePosPoints = [
         Point3(0.24, 0.09, -0.38), VBase3(-1.152, 86.581, -76.784)]
    tapeScaleUpPoint = Point3(0.9, 0.9, 0.24)
    propTrack = Sequence(getPropAppearTrack(tape, suit.getRightHand(), tapePosPoints, 0.8, tapeScaleUpPoint, scaleUpTime=0.5))
    propTrack.append(Wait(1.73))
    hitPoint = lambda toon=toon: __toonTorsoPoint(toon)
    propTrack.append(getPropThrowTrack(attack, tape, [hitPoint], [__toonGroundPoint(attack, toon, 0.7)]))
    hips = toon.getHipsParts()
    animal = toon.style.getAnimal()
    scale = ToontownGlobals.toonBodyScales[animal]
    legs = toon.style.legs
    torso = toon.style.torso
    torso = torso[0]
    animal = animal[0]
    tubeHeight = -0.8
    if torso == 's':
        scaleUpPoint = Point3(scale * 2.03, scale * 2.03, scale * 0.7975)
    else:
        if torso == 'm':
            scaleUpPoint = Point3(scale * 2.03, scale * 2.03, scale * 0.7975)
        else:
            if torso == 'l':
                scaleUpPoint = Point3(scale * 2.03, scale * 2.03, scale * 1.11)
        if animal == 'h' or animal == 'd':
            tubeHeight = -0.87
            scaleUpPoint = Point3(scale * 1.69, scale * 1.69, scale * 0.67)
        tubePosPoints = [
         Point3(0, 0, tubeHeight), MovieUtil.PNT3_ZERO]
        tubeTracks = Parallel()
        tubeTracks.append(Func(battle.movie.needRestoreHips))
        for partNum in range(0, hips.getNumPaths()):
            nextPart = hips.getPath(partNum)
            tubeTracks.append(getPropTrack(tubes[partNum], nextPart, tubePosPoints, 3.25, 3.17, scaleUpPoint=scaleUpPoint))

        tubeTracks.append(Func(battle.movie.clearRestoreHips))
        toonTrack = getToonTrack(attack, 3.4, ['struggle'], 2.8, ['jump'])
        soundTrack = getSoundTrack('SA_red_tape.ogg', delay=2.9, node=suit)
        if dmg > 0:
            return Parallel(suitTrack, toonTrack, propTrack, soundTrack, tubeTracks)
    return Parallel(suitTrack, toonTrack, propTrack, soundTrack)


def doParadigmShift(attack):
    suit = attack['suit']
    battle = attack['battle']
    targets = attack['target']
    hitAtleastOneToon = 0
    for t in targets:
        if t['hp'] > 0:
            hitAtleastOneToon = 1

    damageDelay = 1.95
    dodgeDelay = 0.95
    sprayEffect = BattleParticles.createParticleEffect('ShiftSpray')
    suitName = suit.getStyleName()
    if suitName == 'm':
        sprayEffect.setPos(Point3(-5.2, 4.6, 2.7))
    else:
        if suitName == 'sd':
            sprayEffect.setPos(Point3(-5.2, 4.6, 2.7))
        else:
            sprayEffect.setPos(Point3(0.1, 4.6, 2.7))
    suitTrack = getSuitAnimTrack(attack)
    sprayTrack = getPartTrack(sprayEffect, 1.0, 1.9, [sprayEffect, suit, 0])
    liftTracks = Parallel()
    toonRiseTracks = Parallel()
    for t in targets:
        toon = t['toon']
        dmg = t['hp']
        if dmg > 0:
            liftEffect = BattleParticles.createParticleEffect('ShiftLift')
            liftEffect.setPos(toon.getPos(battle))
            liftEffect.setZ(liftEffect.getZ() - 1.3)
            liftTracks.append(getPartTrack(liftEffect, 1.1, 4.1, [liftEffect, battle, 0]))
            shadow = toon.dropShadow
            fakeShadow = MovieUtil.copyProp(shadow)
            x = toon.getX()
            y = toon.getY()
            z = toon.getZ()
            height = 3
            groundPoint = Point3(x, y, z)
            risePoint = Point3(x, y, z + height)
            shakeRight = Point3(x, y + 0.7, z + height)
            shakeLeft = Point3(x, y - 0.7, z + height)
            shakeTrack = Sequence()
            shakeTrack.append(Wait(damageDelay + 0.25))
            shakeTrack.append(Func(shadow.hide))
            shakeTrack.append(LerpPosInterval(toon, 1.1, risePoint))
            for i in range(0, 17):
                shakeTrack.append(LerpPosInterval(toon, 0.03, shakeLeft))
                shakeTrack.append(LerpPosInterval(toon, 0.03, shakeRight))

            shakeTrack.append(LerpPosInterval(toon, 0.1, risePoint))
            shakeTrack.append(LerpPosInterval(toon, 0.1, groundPoint))
            shakeTrack.append(Func(shadow.show))
            shadowTrack = Sequence()
            shadowTrack.append(Func(battle.movie.needRestoreRenderProp, fakeShadow))
            shadowTrack.append(Wait(damageDelay + 0.25))
            shadowTrack.append(Func(fakeShadow.hide))
            shadowTrack.append(Func(fakeShadow.setScale, 0.27))
            shadowTrack.append(Func(fakeShadow.reparentTo, toon))
            shadowTrack.append(Func(fakeShadow.setPos, MovieUtil.PNT3_ZERO))
            shadowTrack.append(Func(fakeShadow.wrtReparentTo, battle))
            shadowTrack.append(Func(fakeShadow.show))
            shadowTrack.append(LerpScaleInterval(fakeShadow, 0.4, Point3(0.17, 0.17, 0.17)))
            shadowTrack.append(Wait(1.81))
            shadowTrack.append(LerpScaleInterval(fakeShadow, 0.1, Point3(0.27, 0.27, 0.27)))
            shadowTrack.append(Func(MovieUtil.removeProp, fakeShadow))
            shadowTrack.append(Func(battle.movie.clearRenderProp, fakeShadow))
            toonRiseTracks.append(Parallel(shakeTrack, shadowTrack))

    damageAnims = []
    damageAnims.extend(getSplicedLerpAnims('think', 0.66, 1.9, startTime=2.06))
    damageAnims.append(['slip-backward', 0.01, 0.5])
    dodgeAnims = []
    dodgeAnims.append(['jump',
     0.01,
     0,
     0.6])
    dodgeAnims.extend(getSplicedLerpAnims('jump', 0.31, 1.0, startTime=0.6))
    dodgeAnims.append(['jump', 0, 0.91])
    toonTracks = getToonTracks(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, splicedDodgeAnims=dodgeAnims, showDamageExtraTime=2.7)
    if hitAtleastOneToon == 1:
        soundTrack = getSoundTrack('SA_paradigm_shift.ogg', delay=2.1, node=suit)
        return Parallel(suitTrack, sprayTrack, soundTrack, liftTracks, toonTracks, toonRiseTracks)
    return Parallel(suitTrack, sprayTrack, liftTracks, toonTracks, toonRiseTracks)


def doPowerTrip(attack):
    suit = attack['suit']
    battle = attack['battle']
    centerColor = Vec4(0.1, 0.1, 0.1, 0.4)
    edgeColor = Vec4(0.4, 0.1, 0.9, 0.7)
    powerBar1 = BattleParticles.createParticleEffect(file='powertrip')
    powerBar2 = BattleParticles.createParticleEffect(file='powertrip2')
    powerBar1.setPos(0, 6.1, 0.4)
    powerBar1.setHpr(-60, 0, 0)
    powerBar2.setPos(0, 6.1, 0.4)
    powerBar2.setHpr(60, 0, 0)
    powerBar1Particles = powerBar1.getParticlesNamed('particles-1')
    powerBar2Particles = powerBar2.getParticlesNamed('particles-1')
    powerBar1Particles.renderer.setCenterColor(centerColor)
    powerBar1Particles.renderer.setEdgeColor(edgeColor)
    powerBar2Particles.renderer.setCenterColor(centerColor)
    powerBar2Particles.renderer.setEdgeColor(edgeColor)
    waterfallEffect = BattleParticles.createParticleEffect('Waterfall')
    waterfallEffect.setScale(11)
    waterfallParticles = waterfallEffect.getParticlesNamed('particles-1')
    waterfallParticles.renderer.setCenterColor(centerColor)
    waterfallParticles.renderer.setEdgeColor(edgeColor)
    suitName = suit.getStyleName()
    if suitName == 'mh' or suitName == 'sm':
        waterfallEffect.setPos(0, 4, 3.6)
    suitTrack = getSuitAnimTrack(attack)

    def getPowerTrack(effect, suit=suit, battle=battle):
        partTrack = Sequence(Wait(1.0), Func(battle.movie.needRestoreParticleEffect, effect), Func(effect.start, suit), Wait(0.4), LerpPosInterval(effect, 1.0, Point3(0, 15, 0.4)), LerpFunctionInterval(effect.setAlphaScale, fromData=1, toData=0, duration=0.4), Func(effect.cleanup), Func(battle.movie.clearRestoreParticleEffect, effect))
        return partTrack

    partTrack1 = getPowerTrack(powerBar1)
    partTrack2 = getPowerTrack(powerBar2)
    waterfallTrack = getPartTrack(waterfallEffect, 0.6, 1.3, [waterfallEffect, suit, 0])
    toonTracks = getToonTracks(attack, 1.8, ['slip-forward'], 1.29, ['jump'])
    return Parallel(suitTrack, partTrack1, partTrack2, waterfallTrack, toonTracks)


def getThrowEndPoint(suit, toon, battle, whichBounce):
    pnt = toon.getPos(toon)
    if whichBounce == 'one':
        pnt.setY(pnt[1] + 8)
    else:
        if whichBounce == 'two':
            pnt.setY(pnt[1] + 5)
        else:
            if whichBounce == 'threeHit':
                pnt.setZ(pnt[2] + toon.shoulderHeight + 0.3)
            else:
                if whichBounce == 'threeMiss':
                    pass
                else:
                    if whichBounce == 'four':
                        pnt.setY(pnt[1] - 5)
    return Point3(pnt)


def doBounceCheck(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    battle = attack['battle']
    toon = target['toon']
    dmg = target['hp']
    hitSuit = dmg > 0
    check = globalPropPool.getProp('bounced-check')
    checkPosPoints = [MovieUtil.PNT3_ZERO, VBase3(95.247, 79.025, 88.849)]
    bounce1Point = lambda suit=suit, toon=toon, battle=battle: getThrowEndPoint(suit, toon, battle, 'one')
    bounce2Point = lambda suit=suit, toon=toon, battle=battle: getThrowEndPoint(suit, toon, battle, 'two')
    hit3Point = lambda suit=suit, toon=toon, battle=battle: getThrowEndPoint(suit, toon, battle, 'threeHit')
    miss3Point = lambda suit=suit, toon=toon, battle=battle: getThrowEndPoint(suit, toon, battle, 'threeMiss')
    bounce4Point = lambda suit=suit, toon=toon, battle=battle: getThrowEndPoint(suit, toon, battle, 'four')
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        throwDelay = 2.5
        dodgeDelay = 4.3
        damageDelay = 5.1
    else:
        if suitType == 'b':
            throwDelay = 1.8
            dodgeDelay = 3.6
            damageDelay = 4.4
        else:
            if suitType == 'c':
                throwDelay = 1.8
                dodgeDelay = 3.6
                damageDelay = 4.4
    suitTrack = getSuitTrack(attack)
    checkPropTrack = Sequence(getPropAppearTrack(check, suit.getRightHand(), checkPosPoints, 1e-05, Point3(8.5, 8.5, 8.5), startScale=MovieUtil.PNT3_ONE))
    checkPropTrack.append(Wait(throwDelay))
    checkPropTrack.append(Func(check.wrtReparentTo, toon))
    checkPropTrack.append(Func(check.setHpr, Point3(0, -90, 0)))
    checkPropTrack.append(getThrowTrack(check, bounce1Point, duration=0.5, parent=toon))
    checkPropTrack.append(getThrowTrack(check, bounce2Point, duration=0.9, parent=toon))
    if hitSuit:
        checkPropTrack.append(getThrowTrack(check, hit3Point, duration=0.7, parent=toon))
    else:
        checkPropTrack.append(getThrowTrack(check, miss3Point, duration=0.7, parent=toon))
        checkPropTrack.append(getThrowTrack(check, bounce4Point, duration=0.7, parent=toon))
        checkPropTrack.append(LerpScaleInterval(check, 0.3, MovieUtil.PNT3_NEARZERO))
    checkPropTrack.append(Func(MovieUtil.removeProp, check))
    toonTrack = getToonTrack(attack, damageDelay, ['conked'], dodgeDelay, ['sidestep'])
    soundTracks = Sequence(getSoundTrack('SA_pink_slip.ogg', delay=throwDelay + 0.5, duration=0.6, node=suit), getSoundTrack('SA_pink_slip.ogg', delay=0.4, duration=0.6, node=suit))
    return Parallel(suitTrack, checkPropTrack, toonTrack, soundTracks)


def doWatercooler(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    watercooler = globalPropPool.getProp('watercooler')

    def getCoolerSpout(watercooler=watercooler):
        spout = watercooler.find('**/joint_toSpray')
        return spout.getPos(render)

    hitPoint = lambda toon=toon: __toonFacePoint(toon)
    missPoint = lambda prop=watercooler, toon=toon: __toonMissPoint(prop, toon, 0, parent=render)
    hitSprayTrack = MovieUtil.getSprayTrack(battle, Point4(0.75, 0.75, 1.0, 0.8), getCoolerSpout, hitPoint, 0.2, 0.2, 0.2, horizScale=0.3, vertScale=0.3)
    missSprayTrack = MovieUtil.getSprayTrack(battle, Point4(0.75, 0.75, 1.0, 0.8), getCoolerSpout, missPoint, 0.2, 0.2, 0.2, horizScale=0.3, vertScale=0.3)
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(0.48, 0.11, -0.92), VBase3(20.403, 33.158, 69.511)]
    propTrack = Sequence(Wait(1.01), Func(__showProp, watercooler, suit.getLeftHand(), posPoints[0], posPoints[1]), LerpScaleInterval(watercooler, 0.5, Point3(1.15, 1.15, 1.15)), Wait(1.6))
    if dmg > 0:
        propTrack.append(hitSprayTrack)
    else:
        propTrack.append(missSprayTrack)
    propTrack += [Wait(0.01), LerpScaleInterval(watercooler, 0.5, MovieUtil.PNT3_NEARZERO), Func(MovieUtil.removeProp, watercooler)]
    splashTrack = Sequence()
    if dmg > 0:

        def prepSplash(splash, targetPoint):
            splash.reparentTo(render)
            splash.setPos(targetPoint)
            scale = splash.getScale()
            splash.setBillboardPointWorld()
            splash.setScale(scale)

        splash = globalPropPool.getProp('splash-from-splat')
        splash.setColor(0.75, 0.75, 1, 0.8)
        splash.setScale(0.3)
        splashTrack = Sequence(Func(battle.movie.needRestoreRenderProp, splash), Wait(3.2), Func(prepSplash, splash, __toonFacePoint(toon)), ActorInterval(splash, 'splash-from-splat'), Func(MovieUtil.removeProp, splash), Func(battle.movie.clearRenderProp, splash))
    toonTrack = getToonTrack(attack, suitTrack.getDuration() - 1.5, ['cringe'], 2.4, ['sidestep'])
    soundTrack = Sequence(Wait(1.1), SoundInterval(globalBattleSoundCache.getSound('SA_watercooler_appear_only.ogg'), node=suit, duration=1.4722), Wait(0.4), SoundInterval(globalBattleSoundCache.getSound('SA_watercooler_spray_only.ogg'), node=suit, duration=2.313))
    return Parallel(suitTrack, toonTrack, propTrack, soundTrack, splashTrack)


def doFired(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    BattleParticles.loadParticles()
    baseFlameEffect = BattleParticles.createParticleEffect(file='firedBaseFlame')
    flameEffect = BattleParticles.createParticleEffect('FiredFlame')
    flecksEffect = BattleParticles.createParticleEffect('SpriteFiredFlecks')
    BattleParticles.setEffectTexture(baseFlameEffect, 'fire')
    BattleParticles.setEffectTexture(flameEffect, 'fire')
    BattleParticles.setEffectTexture(flecksEffect, 'roll-o-dex', color=Vec4(0.8, 0.8, 0.8, 1))
    baseFlameSmall = BattleParticles.createParticleEffect(file='firedBaseFlame')
    flameSmall = BattleParticles.createParticleEffect('FiredFlame')
    flecksSmall = BattleParticles.createParticleEffect('SpriteFiredFlecks')
    BattleParticles.setEffectTexture(baseFlameSmall, 'fire')
    BattleParticles.setEffectTexture(flameSmall, 'fire')
    BattleParticles.setEffectTexture(flecksSmall, 'roll-o-dex', color=Vec4(0.8, 0.8, 0.8, 1))
    baseFlameSmall.setScale(0.7)
    flameSmall.setScale(0.7)
    flecksSmall.setScale(0.7)
    suitTrack = getSuitTrack(attack)
    baseFlameTrack = getPartTrack(baseFlameEffect, 1.0, 1.9, [baseFlameEffect, toon, 0])
    flameTrack = getPartTrack(flameEffect, 1.0, 1.9, [flameEffect, toon, 0])
    flecksTrack = getPartTrack(flecksEffect, 1.8, 1.1, [flecksEffect, toon, 0])
    baseFlameSmallTrack = getPartTrack(baseFlameSmall, 1.0, 1.9, [baseFlameSmall, toon, 0])
    flameSmallTrack = getPartTrack(flameSmall, 1.0, 1.9, [flameSmall, toon, 0])
    flecksSmallTrack = getPartTrack(flecksSmall, 1.8, 1.1, [flecksSmall, toon, 0])

    def changeColor(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(Func(nextPart.setColorScale, Vec4(0, 0, 0, 1)))

        return track

    def resetColor(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(Func(nextPart.clearColorScale))

        return track

    if dmg > 0:
        headParts = toon.getHeadParts()
        torsoParts = toon.getTorsoParts()
        legsParts = toon.getLegsParts()
        colorTrack = Sequence()
        colorTrack.append(Wait(2.0))
        colorTrack.append(Func(battle.movie.needRestoreColor))
        colorTrack.append(changeColor(headParts))
        colorTrack.append(changeColor(torsoParts))
        colorTrack.append(changeColor(legsParts))
        colorTrack.append(Wait(3.5))
        colorTrack.append(resetColor(headParts))
        colorTrack.append(resetColor(torsoParts))
        colorTrack.append(resetColor(legsParts))
        colorTrack.append(Func(battle.movie.clearRestoreColor))
    damageAnims = []
    damageAnims.append(['cringe',
     0.01,
     0.7,
     0.62])
    damageAnims.append(['slip-forward',
     1e-05,
     0.4,
     1.2])
    damageAnims.extend(getSplicedLerpAnims('slip-forward', 0.31, 0.8, startTime=1.2))
    toonTrack = getToonTrack(attack, damageDelay=1.5, splicedDamageAnims=damageAnims, dodgeDelay=0.3, dodgeAnimNames=['sidestep'])
    soundTrack = getSoundTrack('SA_hot_air.ogg', delay=1.0, node=suit)
    if dmg > 0:
        return Parallel(suitTrack, baseFlameTrack, flameTrack, flecksTrack, toonTrack, colorTrack, soundTrack)
    return Parallel(suitTrack, baseFlameSmallTrack, flameSmallTrack, flecksSmallTrack, toonTrack, soundTrack)


def doAudit(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    calculator = globalPropPool.getProp('calculator')
    BattleParticles.loadParticles()
    particleEffect = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect, 'audit-one', color=Vec4(0, 0, 0, 1))
    particleEffect2 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect2, 'audit-two', color=Vec4(0, 0, 0, 1))
    particleEffect3 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect3, 'audit-three', color=Vec4(0, 0, 0, 1))
    particleEffect4 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect4, 'audit-four', color=Vec4(0, 0, 0, 1))
    particleEffect5 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect5, 'audit-mult', color=Vec4(0, 0, 0, 1))
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(particleEffect, 2.1, 1.9, [particleEffect, suit, 0])
    partTrack2 = getPartTrack(particleEffect2, 2.2, 2.0, [particleEffect2, suit, 0])
    partTrack3 = getPartTrack(particleEffect3, 2.3, 2.1, [particleEffect3, suit, 0])
    partTrack4 = getPartTrack(particleEffect4, 2.4, 2.2, [particleEffect4, suit, 0])
    partTrack5 = getPartTrack(particleEffect5, 2.5, 2.3, [particleEffect5, suit, 0])
    suitName = attack['suitName']
    if suitName == 'nc':
        calcPosPoints = [
         Point3(-0.15, 0.37, 0.03), VBase3(1.352, -6.518, -6.045)]
        calcDuration = 0.76
        scaleUpPoint = Point3(1.1, 1.85, 1.81)
    else:
        calcPosPoints = [
         Point3(0.35, 0.52, 0.03), VBase3(1.352, -6.518, -6.045)]
        calcDuration = 1.87
        scaleUpPoint = Point3(1.0, 1.37, 1.31)
    calcPropTrack = getPropTrack(calculator, suit.getLeftHand(), calcPosPoints, 1e-06, calcDuration, scaleUpPoint=scaleUpPoint, anim=1, propName='calculator', animStartTime=0.5, animDuration=3.4)
    toonTrack = getToonTrack(attack, 3.2, ['conked'], 0.9, ['duck'], showMissedExtraTime=2.2)
    soundTrack = getSoundTrack('SA_audit.ogg', delay=1.9, node=suit)
    return Parallel(suitTrack, toonTrack, calcPropTrack, soundTrack, partTrack, partTrack2, partTrack3, partTrack4, partTrack5)


def doCalculate(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    calculator = globalPropPool.getProp('calculator')
    BattleParticles.loadParticles()
    particleEffect = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect, 'audit-one', color=Vec4(0, 0, 0, 1))
    particleEffect2 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect2, 'audit-plus', color=Vec4(0, 0, 0, 1))
    particleEffect3 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect3, 'audit-mult', color=Vec4(0, 0, 0, 1))
    particleEffect4 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect4, 'audit-three', color=Vec4(0, 0, 0, 1))
    particleEffect5 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect5, 'audit-div', color=Vec4(0, 0, 0, 1))
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(particleEffect, 2.1, 1.9, [particleEffect, suit, 0])
    partTrack2 = getPartTrack(particleEffect2, 2.2, 2.0, [particleEffect2, suit, 0])
    partTrack3 = getPartTrack(particleEffect3, 2.3, 2.1, [particleEffect3, suit, 0])
    partTrack4 = getPartTrack(particleEffect4, 2.4, 2.2, [particleEffect4, suit, 0])
    partTrack5 = getPartTrack(particleEffect5, 2.5, 2.3, [particleEffect5, suit, 0])
    suitName = attack['suitName']
    if suitName == 'nc':
        calcPosPoints = [
         Point3(-0.15, 0.37, 0.03), VBase3(1.352, -6.518, -6.045)]
        calcDuration = 0.76
        scaleUpPoint = Point3(1.1, 1.85, 1.81)
    else:
        calcPosPoints = [
         Point3(0.35, 0.52, 0.03), VBase3(1.352, -6.518, -6.045)]
        calcDuration = 1.87
        scaleUpPoint = Point3(1.0, 1.37, 1.31)
    calcPropTrack = getPropTrack(calculator, suit.getLeftHand(), calcPosPoints, 1e-06, calcDuration, scaleUpPoint=scaleUpPoint, anim=1, propName='calculator', animStartTime=0.5, animDuration=3.4)
    toonTrack = getToonTrack(attack, 3.2, ['conked'], 1.8, ['sidestep'])
    return Parallel(suitTrack, toonTrack, calcPropTrack, partTrack, partTrack2, partTrack3, partTrack4, partTrack5)


def doTabulate(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    calculator = globalPropPool.getProp('calculator')
    BattleParticles.loadParticles()
    particleEffect = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect, 'audit-plus', color=Vec4(0, 0, 0, 1))
    particleEffect2 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect2, 'audit-minus', color=Vec4(0, 0, 0, 1))
    particleEffect3 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect3, 'audit-mult', color=Vec4(0, 0, 0, 1))
    particleEffect4 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect4, 'audit-div', color=Vec4(0, 0, 0, 1))
    particleEffect5 = BattleParticles.createParticleEffect('Calculate')
    BattleParticles.setEffectTexture(particleEffect5, 'audit-one', color=Vec4(0, 0, 0, 1))
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(particleEffect, 2.1, 1.9, [particleEffect, suit, 0])
    partTrack2 = getPartTrack(particleEffect2, 2.2, 2.0, [particleEffect2, suit, 0])
    partTrack3 = getPartTrack(particleEffect3, 2.3, 2.1, [particleEffect3, suit, 0])
    partTrack4 = getPartTrack(particleEffect4, 2.4, 2.2, [particleEffect4, suit, 0])
    partTrack5 = getPartTrack(particleEffect5, 2.5, 2.3, [particleEffect5, suit, 0])
    suitName = attack['suitName']
    if suitName == 'nc':
        calcPosPoints = [
         Point3(-0.15, 0.37, 0.03), VBase3(1.352, -6.518, -6.045)]
        calcDuration = 0.76
        scaleUpPoint = Point3(1.1, 1.85, 1.81)
    else:
        calcPosPoints = [
         Point3(0.35, 0.52, 0.03), VBase3(1.352, -6.518, -6.045)]
        calcDuration = 1.87
        scaleUpPoint = Point3(1.0, 1.37, 1.31)
    calcPropTrack = getPropTrack(calculator, suit.getLeftHand(), calcPosPoints, 1e-06, calcDuration, scaleUpPoint=scaleUpPoint, anim=1, propName='calculator', animStartTime=0.5, animDuration=3.4)
    toonTrack = getToonTrack(attack, 3.2, ['conked'], 1.8, ['sidestep'])
    return Parallel(suitTrack, toonTrack, calcPropTrack, partTrack, partTrack2, partTrack3, partTrack4, partTrack5)


def doCrunch(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    throwDuration = 3.03
    suitTrack = getSuitTrack(attack)
    numberNames = ['one',
     'two',
     'three',
     'four',
     'five',
     'six']
    BattleParticles.loadParticles()
    numberSpill1 = BattleParticles.createParticleEffect(file='numberSpill')
    numberSpill2 = BattleParticles.createParticleEffect(file='numberSpill')
    spillTexture1 = random.choice(numberNames)
    spillTexture2 = random.choice(numberNames)
    BattleParticles.setEffectTexture(numberSpill1, 'audit-' + spillTexture1)
    BattleParticles.setEffectTexture(numberSpill2, 'audit-' + spillTexture2)
    numberSpillTrack1 = getPartTrack(numberSpill1, 1.1, 2.2, [numberSpill1, suit, 0])
    numberSpillTrack2 = getPartTrack(numberSpill2, 1.5, 1.0, [numberSpill2, suit, 0])
    numberSprayTracks = Parallel()
    numOfNumbers = random.randint(5, 9)
    for i in range(0, numOfNumbers - 1):
        nextSpray = BattleParticles.createParticleEffect(file='numberSpray')
        nextTexture = random.choice(numberNames)
        BattleParticles.setEffectTexture(nextSpray, 'audit-' + nextTexture)
        nextStartTime = random.random() * 0.6 + throwDuration
        nextDuration = random.random() * 0.4 + 1.4
        nextSprayTrack = getPartTrack(nextSpray, nextStartTime, nextDuration, [nextSpray, suit, 0])
        numberSprayTracks.append(nextSprayTrack)

    numberTracks = Parallel()
    for i in range(0, numOfNumbers):
        texture = random.choice(numberNames)
        next = MovieUtil.copyProp(BattleParticles.getParticle('audit-' + texture))
        next.reparentTo(suit.getRightHand())
        next.setScale(0.01, 0.01, 0.01)
        next.setColor(Vec4(0.0, 0.0, 0.0, 1.0))
        next.setPos(random.random() * 0.6 - 0.3, random.random() * 0.6 - 0.3, random.random() * 0.6 - 0.3)
        next.setHpr(VBase3(-1.15, 86.58, -76.78))
        numberTrack = Sequence(Wait(0.9), LerpScaleInterval(next, 0.6, MovieUtil.PNT3_ONE), Wait(1.7), Func(MovieUtil.removeProp, next))
        numberTracks.append(numberTrack)

    damageAnims = []
    damageAnims.append(['cringe',
     0.01,
     0.14,
     0.28])
    damageAnims.append(['cringe',
     0.01,
     0.16,
     0.3])
    damageAnims.append(['cringe',
     0.01,
     0.13,
     0.22])
    damageAnims.append(['slip-forward', 0.01, 0.6])
    toonTrack = getToonTrack(attack, damageDelay=4.7, splicedDamageAnims=damageAnims, dodgeDelay=3.6, dodgeAnimNames=['sidestep'])
    return Parallel(suitTrack, toonTrack, numberSpillTrack1, numberSpillTrack2, numberTracks, numberSprayTracks)


def doLiquidate(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    dmg = target['hp']
    toon = target['toon']
    BattleParticles.loadParticles()
    rainEffect = BattleParticles.createParticleEffect(file='liquidate')
    rainEffect2 = BattleParticles.createParticleEffect(file='liquidate')
    rainEffect3 = BattleParticles.createParticleEffect(file='liquidate')
    cloud = globalPropPool.getProp('stormcloud')
    suitType = getSuitBodyType(attack['suitName'])
    if suitType == 'a':
        partDelay = 0.2
        damageDelay = 3.5
        dodgeDelay = 2.45
    else:
        if suitType == 'b':
            partDelay = 0.2
            damageDelay = 3.5
            dodgeDelay = 2.45
        else:
            if suitType == 'c':
                partDelay = 0.2
                damageDelay = 3.5
                dodgeDelay = 2.45
        suitTrack = getSuitTrack(attack, delay=0.9)
        initialCloudHeight = suit.height + 3
        cloudPosPoints = [Point3(0, 3, initialCloudHeight), VBase3(180, 0, 0)]
        cloudPropTrack = Sequence()
        cloudPropTrack.append(Func(cloud.pose, 'stormcloud', 0))
        cloudPropTrack.append(getPropAppearTrack(cloud, suit, cloudPosPoints, 1e-06, Point3(3, 3, 3), scaleUpTime=0.7))
        cloudPropTrack.append(Func(battle.movie.needRestoreRenderProp, cloud))
        cloudPropTrack.append(Func(cloud.wrtReparentTo, render))
        targetPoint = __toonFacePoint(toon)
        targetPoint.setZ(targetPoint[2] + 3)
        cloudPropTrack.append(Wait(1.1))
        cloudPropTrack.append(LerpPosInterval(cloud, 1, pos=targetPoint))
        cloudPropTrack.append(Wait(partDelay))
        cloudPropTrack.append(Parallel(Sequence(ParticleInterval(rainEffect, cloud, worldRelative=0, duration=2.1, cleanup=True)), Sequence(Wait(0.1), ParticleInterval(rainEffect2, cloud, worldRelative=0, duration=2.0, cleanup=True)), Sequence(Wait(0.1), ParticleInterval(rainEffect3, cloud, worldRelative=0, duration=2.0, cleanup=True)), Sequence(ActorInterval(cloud, 'stormcloud', startTime=3, duration=0.1), ActorInterval(cloud, 'stormcloud', startTime=1, duration=2.3))))
        cloudPropTrack.append(Wait(0.4))
        cloudPropTrack.append(LerpScaleInterval(cloud, 0.5, MovieUtil.PNT3_NEARZERO))
        cloudPropTrack.append(Func(MovieUtil.removeProp, cloud))
        cloudPropTrack.append(Func(battle.movie.clearRenderProp, cloud))
        if not toon.isDisguised:
            damageAnims = [
             [
              'melt'], ['jump', 1.5, 0.4]]
            toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, dodgeAnimNames=['sidestep'])
        else:
            toonTrack = getToonTrack(attack, 3.5, ['suitQuicksandAnim'], 2.45, ['sidestep'])
        soundTrack = getSoundTrack('SA_liquidate.ogg', delay=2.0, node=suit)
        if dmg > 0:
            puddle = globalPropPool.getProp('quicksand')
            puddle.setColor(Vec4(0.0, 0.0, 1.0, 1))
            puddle.setHpr(Point3(120, 0, 0))
            puddle.setScale(0.01)
            puddleTrack = Sequence(Func(battle.movie.needRestoreRenderProp, puddle), Wait(damageDelay - 0.7), Func(puddle.reparentTo, battle), Func(puddle.setPos, toon.getPos(battle)), LerpScaleInterval(puddle, 1.7, Point3(1.7, 1.7, 1.7), startScale=MovieUtil.PNT3_NEARZERO), Wait(3.2), LerpFunctionInterval(puddle.setAlphaScale, fromData=1, toData=0, duration=0.8), Func(MovieUtil.removeProp, puddle), Func(battle.movie.clearRenderProp, puddle))
            if toon.isDisguised:
                toonTrack = getToonTrack(attack, 3.5, ['suitQuicksandAnim'], 2.45, ['sidestep'], flexOnEx=1, prop=puddle)
            return Parallel(suitTrack, toonTrack, cloudPropTrack, soundTrack, puddleTrack)
    return Parallel(suitTrack, toonTrack, cloudPropTrack, soundTrack)


def doPushSwitch(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    button = globalPropPool.getProp('button')
    button.setP(180)
    suitTrack = getSuitTrack(attack)
    buttonTrack = Sequence(Func(button.reparentTo, suit.getLeftHand()), button.scaleInterval(0.5, Vec3(1, 1, 1), startScale=Vec3(0, 0, 0)), Wait(4.5), button.scaleInterval(1, Vec3(0, 0, 0), startScale=Vec3(1, 1, 1)))
    dropDelay = 5
    sandbag = globalPropPool.getProp('sandbag')
    dropSequence = Sequence()
    dropSequence.append(Wait(dropDelay))
    dropSequence.append(Func(sandbag.reparentTo, toon))
    if dmg > 0:
        dropSequence.append(Func(sandbag.setZ, toon.getHeight()))
    dropSequence.append(ActorInterval(sandbag, 'sandbag'))
    dropSequence.append(Func(sandbag.reparentTo, hidden))
    toonTrack = getToonTrack(attack, 5.15, ['slip-backward'], 4.5, ['sidestep'])
    soundTrack = getSoundTrack('SA_pressing_button.ogg', delay=2, node=suit)
    if dmg > 0:
        sandSoundTrack = getSoundTrack('AA_drop_sandbag.ogg', delay=5, node=toon)
    else:
        sandSoundTrack = getSoundTrack('AA_drop_sandbag_miss.ogg', delay=5, node=toon)
    return Parallel(suitTrack, toonTrack, buttonTrack, soundTrack, dropSequence, sandSoundTrack)


def doMarketCrash(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    suitDelay = 1.32
    propDelay = 0.6
    throwDuration = 1.5
    paper = globalPropPool.getProp('newspaper')
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(-0.07, 0.17, -0.13), VBase3(161.867, -33.149, -48.086)]
    paperTrack = Sequence(getPropAppearTrack(paper, suit.getRightHand(), posPoints, propDelay, Point3(3, 3, 3), scaleUpTime=0.5))
    paperTrack.append(Wait(suitDelay))
    hitPoint = toon.getPos(battle)
    hitPoint.setX(hitPoint.getX() + 1.2)
    hitPoint.setY(hitPoint.getY() + 1.5)
    if dmg > 0:
        hitPoint.setZ(hitPoint.getZ() + 1.1)
    movePoint = Point3(hitPoint.getX(), hitPoint.getY() - 1.8, hitPoint.getZ() + 0.2)
    paperTrack.append(Func(battle.movie.needRestoreRenderProp, paper))
    paperTrack.append(Func(paper.wrtReparentTo, battle))
    paperTrack.append(getThrowTrack(paper, hitPoint, duration=throwDuration, parent=battle))
    paperTrack.append(Wait(0.6))
    paperTrack.append(LerpPosInterval(paper, 0.4, movePoint))
    spinTrack = Sequence(Wait(propDelay + suitDelay + 0.2), LerpHprInterval(paper, throwDuration, Point3(-360, 0, 0)))
    sizeTrack = Sequence(Wait(propDelay + suitDelay + 0.2), LerpScaleInterval(paper, throwDuration, Point3(6, 6, 6)), Wait(0.95), LerpScaleInterval(paper, 0.4, MovieUtil.PNT3_NEARZERO))
    propTrack = Sequence(Parallel(paperTrack, spinTrack, sizeTrack), Func(MovieUtil.removeProp, paper), Func(battle.movie.clearRenderProp, paper))
    damageAnims = []
    damageAnims.append(['cringe',
     0.01,
     0.21,
     0.08])
    damageAnims.append(['slip-forward',
     0.01,
     0.6,
     0.85])
    damageAnims.extend(getSplicedLerpAnims('slip-forward', 0.31, 0.95, startTime=1.2))
    damageAnims.append(['slip-forward', 0.01, 1.51])
    toonTrack = getToonTrack(attack, damageDelay=3.8, splicedDamageAnims=damageAnims, dodgeDelay=2.4, dodgeAnimNames=['sidestep'], showDamageExtraTime=0.4, showMissedExtraTime=1.3)
    return Parallel(suitTrack, toonTrack, propTrack)


def doBite(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    teeth = globalPropPool.getProp('teeth')
    propDelay = 0.8
    propScaleUpTime = 0.5
    suitDelay = 1.73
    throwDelay = propDelay + propScaleUpTime + suitDelay
    throwDuration = 0.4
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(-0.05, 0.41, -0.54), VBase3(4.465, -3.563, 51.479)]
    teethAppearTrack = Sequence(getPropAppearTrack(teeth, suit.getRightHand(), posPoints, propDelay, Point3(3, 3, 3), scaleUpTime=propScaleUpTime))
    teethAppearTrack.append(Wait(suitDelay))
    teethAppearTrack.append(Func(battle.movie.needRestoreRenderProp, teeth))
    teethAppearTrack.append(Func(teeth.wrtReparentTo, battle))
    if dmg > 0:
        x = toon.getX(battle)
        y = toon.getY(battle)
        z = toon.getZ(battle)
        toonHeight = z + toon.getHeight()
        flyPoint = Point3(x, y + 2.7, toonHeight * 0.8)
        teethAppearTrack.append(LerpPosInterval(teeth, throwDuration, pos=flyPoint))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.4, pos=Point3(x, y + 3.2, toonHeight * 0.7)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.3, pos=Point3(x, y + 4.7, toonHeight * 0.5)))
        teethAppearTrack.append(Wait(0.2))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.1, pos=Point3(x, y - 0.2, toonHeight * 0.9)))
        teethAppearTrack.append(Wait(0.4))
        scaleTrack = Sequence(Wait(throwDelay), LerpScaleInterval(teeth, throwDuration, Point3(8, 8, 8)), Wait(0.9), LerpScaleInterval(teeth, 0.2, Point3(14, 14, 14)), Wait(1.2), LerpScaleInterval(teeth, 0.3, MovieUtil.PNT3_NEARZERO))
        hprTrack = Sequence(Wait(throwDelay), LerpHprInterval(teeth, 0.3, Point3(180, 0, 0)), Wait(0.2), LerpHprInterval(teeth, 0.4, Point3(180, -35, 0), startHpr=Point3(180, 0, 0)), Wait(0.6), LerpHprInterval(teeth, 0.1, Point3(180, -75, 0), startHpr=Point3(180, -35, 0)))
        animTrack = Sequence(Wait(throwDelay), ActorInterval(teeth, 'teeth', duration=throwDuration), ActorInterval(teeth, 'teeth', duration=0.3), Func(teeth.pose, 'teeth', 1), Wait(0.7), ActorInterval(teeth, 'teeth', duration=0.9))
        propTrack = Sequence(Parallel(teethAppearTrack, scaleTrack, hprTrack, animTrack), Func(MovieUtil.removeProp, teeth), Func(battle.movie.clearRenderProp, teeth))
    else:
        flyPoint = __toonFacePoint(toon, parent=battle)
        flyPoint.setY(flyPoint.getY() - 7.1)
        teethAppearTrack.append(LerpPosInterval(teeth, throwDuration, pos=flyPoint))
        teethAppearTrack.append(Func(MovieUtil.removeProp, teeth))
        teethAppearTrack.append(Func(battle.movie.clearRenderProp, teeth))
        propTrack = teethAppearTrack
    damageAnims = [
     [
      'cringe',
      0.01,
      0.7,
      1.2],
     ['conked',
      0.01,
      0.2,
      2.1], ['conked', 0.01, 3.2]]
    dodgeAnims = [
     ['cringe',
      0.01,
      0.7,
      0.2], ['duck', 0.01, 1.6]]
    toonTrack = getToonTrack(attack, damageDelay=3.2, splicedDamageAnims=damageAnims, dodgeDelay=2.9, splicedDodgeAnims=dodgeAnims, showDamageExtraTime=2.4)
    return Parallel(suitTrack, toonTrack, propTrack)


def doChomp(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    teeth = globalPropPool.getProp('teeth')
    propDelay = 0.8
    propScaleUpTime = 0.5
    suitDelay = 1.73
    throwDelay = propDelay + propScaleUpTime + suitDelay
    throwDuration = 0.4
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(-0.05, 0.41, -0.54), VBase3(4.465, -3.563, 51.479)]
    teethAppearTrack = Sequence(getPropAppearTrack(teeth, suit.getRightHand(), posPoints, propDelay, Point3(3, 3, 3), scaleUpTime=propScaleUpTime))
    teethAppearTrack.append(Wait(suitDelay))
    teethAppearTrack.append(Func(battle.movie.needRestoreRenderProp, teeth))
    teethAppearTrack.append(Func(teeth.wrtReparentTo, battle))
    if dmg > 0:
        x = toon.getX(battle)
        y = toon.getY(battle)
        z = toon.getZ(battle)
        toonHeight = z + toon.getHeight()
        flyPoint = Point3(x, y + 2.7, toonHeight * 0.7)
        teethAppearTrack.append(LerpPosInterval(teeth, throwDuration, pos=flyPoint))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.4, pos=Point3(x, y + 3.2, toonHeight * 0.7)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.3, pos=Point3(x, y + 4.7, toonHeight * 0.5)))
        teethAppearTrack.append(Wait(0.2))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.1, pos=Point3(x, y, toonHeight + 3)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.1, pos=Point3(x, y - 1.2, toonHeight * 0.7)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.1, pos=Point3(x, y - 0.7, toonHeight * 0.4)))
        teethAppearTrack.append(Wait(0.4))
        scaleTrack = Sequence(Wait(throwDelay), LerpScaleInterval(teeth, throwDuration, Point3(6, 6, 6)), Wait(0.9), LerpScaleInterval(teeth, 0.2, Point3(10, 10, 10)), Wait(1.2), LerpScaleInterval(teeth, 0.3, MovieUtil.PNT3_NEARZERO))
        hprTrack = Sequence(Wait(throwDelay), LerpHprInterval(teeth, 0.3, Point3(180, 0, 0)), Wait(0.2), LerpHprInterval(teeth, 0.4, Point3(180, -35, 0), startHpr=Point3(180, 0, 0)), Wait(0.6), LerpHprInterval(teeth, 0.1, Point3(0, -35, 0), startHpr=Point3(180, -35, 0)))
        animTrack = Sequence(Wait(throwDelay), ActorInterval(teeth, 'teeth', duration=throwDuration), ActorInterval(teeth, 'teeth', duration=0.3), Func(teeth.pose, 'teeth', 1), Wait(0.7), ActorInterval(teeth, 'teeth', duration=0.9))
        propTrack = Sequence(Parallel(teethAppearTrack, scaleTrack, hprTrack, animTrack), Func(MovieUtil.removeProp, teeth), Func(battle.movie.clearRenderProp, teeth))
    else:
        x = toon.getX(battle)
        y = toon.getY(battle)
        z = toon.getZ(battle)
        z = z + 0.2
        flyPoint = Point3(x, y - 2.1, z)
        teethAppearTrack.append(LerpPosInterval(teeth, throwDuration, pos=flyPoint))
        teethAppearTrack.append(Wait(0.2))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.2, pos=Point3(x + 0.5, y - 2.5, z)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.2, pos=Point3(x + 1.0, y - 3.0, z + 0.4)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.2, pos=Point3(x + 1.3, y - 3.6, z)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.2, pos=Point3(x + 0.9, y - 3.1, z + 0.4)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.2, pos=Point3(x + 0.3, y - 2.6, z)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.2, pos=Point3(x - 0.1, y - 2.2, z + 0.4)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.2, pos=Point3(x - 0.4, y - 1.9, z)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.2, pos=Point3(x - 0.7, y - 2.1, z + 0.4)))
        teethAppearTrack.append(LerpPosInterval(teeth, 0.2, pos=Point3(x - 0.8, y - 2.3, z)))
        teethAppearTrack.append(LerpScaleInterval(teeth, 0.6, MovieUtil.PNT3_NEARZERO))
        hprTrack = Sequence(Wait(throwDelay), LerpHprInterval(teeth, 0.3, Point3(180, 0, 0)), Wait(0.5), LerpHprInterval(teeth, 0.4, Point3(80, 0, 0), startHpr=Point3(180, 0, 0)), LerpHprInterval(teeth, 0.8, Point3(-10, 0, 0), startHpr=Point3(80, 0, 0)))
        animTrack = Sequence(Wait(throwDelay), ActorInterval(teeth, 'teeth', duration=3.6))
        propTrack = Sequence(Parallel(teethAppearTrack, hprTrack, animTrack), Func(MovieUtil.removeProp, teeth), Func(battle.movie.clearRenderProp, teeth))
    damageAnims = [
     [
      'cringe',
      0.01,
      0.7,
      1.2],
     [
      'spit',
      0.01,
      2.95,
      1.47],
     [
      'spit',
      0.01,
      4.42,
      0.07],
     [
      'spit',
      0.08,
      4.49,
      -0.07],
     [
      'spit',
      0.08,
      4.42,
      0.07],
     [
      'spit',
      0.08,
      4.49,
      -0.07],
     [
      'spit',
      0.08,
      4.42,
      0.07],
     [
      'spit',
      0.08,
      4.49,
      -0.07],
     [
      'spit', 0.01, 4.42]]
    dodgeAnims = [['jump', 0.01, 0.01]]
    toonTrack = getToonTrack(attack, damageDelay=3.2, splicedDamageAnims=damageAnims, dodgeDelay=2.75, splicedDodgeAnims=dodgeAnims, showDamageExtraTime=1.4)
    return Parallel(suitTrack, toonTrack, propTrack)


def doCigar(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    BattleParticles.loadParticles()
    baseFlameEffect = BattleParticles.createParticleEffect(file='cigarSmokeAtk')
    baseFlameSmall = BattleParticles.createParticleEffect(file='cigarSmokeAtk')
    baseFlameSmall.setScale(0.7)
    cigar = globalPropPool.getProp('cigar')
    suitTrack = getSuitTrack(attack)
    if attack['suitName'] == 'sf' and suit.cigar != None:
        propTrack = Sequence(LerpScaleInterval(suit.cigar, 0.5, MovieUtil.PNT3_NEARZERO), Func(suit.cigar.stash), Func(__showProp, cigar, suit.getRightHand(), (-0.34,
                                                                                                                                                                -0.49,
                                                                                                                                                                -0.24), (180.0,
                                                                                                                                                                         0.0,
                                                                                                                                                                         180.0)), LerpScaleInterval(cigar, 0.5, Point3(8.0)), Wait(4.0), Wait(0.01), LerpScaleInterval(cigar, 0.5, MovieUtil.PNT3_NEARZERO), Func(MovieUtil.removeProp, cigar), Func(suit.cigar.unstash), LerpScaleInterval(suit.cigar, 0.5, Point3(8.0)))
    else:
        propTrack = Sequence(Wait(0.5), Func(__showProp, cigar, suit.getRightHand(), (-0.34,
                                                                                      -0.49,
                                                                                      -0.24), (180.0,
                                                                                               0.0,
                                                                                               180.0)), LerpScaleInterval(cigar, 0.5, Point3(8.0)), Wait(4.5), Wait(0.01), LerpScaleInterval(cigar, 0.5, MovieUtil.PNT3_NEARZERO), Func(MovieUtil.removeProp, cigar))
    baseFlameTrack = getPartTrack(baseFlameEffect, 3.8, 1.9, [baseFlameEffect, suit, 0])
    baseFlameSmallTrack = getPartTrack(baseFlameSmall, 3.8, 1.9, [baseFlameSmall, suit, 0])

    def changeColor(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(nextPart.colorScaleInterval(0.1, Vec4(0.5, 0.5, 0.5, 1)))

        return track

    def resetColor(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(Func(nextPart.clearColorScale))

        return track

    if dmg > 0:
        headParts = toon.getHeadParts()
        torsoParts = toon.getTorsoParts()
        legsParts = toon.getLegsParts()
        colorTrack = Sequence()
        colorTrack.append(Wait(4.4))
        colorTrack.append(Func(battle.movie.needRestoreColor))
        colorTrack.append(changeColor(headParts))
        colorTrack.append(changeColor(torsoParts))
        colorTrack.append(changeColor(legsParts))
        colorTrack.append(Wait(3.5))
        colorTrack.append(resetColor(headParts))
        colorTrack.append(resetColor(torsoParts))
        colorTrack.append(resetColor(legsParts))
        colorTrack.append(Func(battle.movie.clearRestoreColor))
    damageAnims = []
    damageAnims.append(['cringe',
     0.01,
     0.7,
     0.62])
    damageAnims.append(['slip-forward',
     1e-05,
     0.4,
     1.2])
    damageAnims.extend(getSplicedLerpAnims('slip-forward', 0.31, 0.8, startTime=4.2))
    toonTrack = getToonTrack(attack, damageDelay=4.8, splicedDamageAnims=damageAnims, dodgeDelay=3.9, dodgeAnimNames=['sidestep'])
    soundTrack = getSoundTrack('SA_filibuster.ogg', delay=4.0, node=suit)
    if dmg > 0:
        return Parallel(suitTrack, propTrack, baseFlameTrack, toonTrack, colorTrack, soundTrack)
    return Parallel(suitTrack, propTrack, baseFlameSmallTrack, toonTrack, soundTrack)
    return


def doEvictionNotice(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    paper = globalPropPool.getProp('shredder-paper')
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(-0.04, 0.15, -1.38), VBase3(10.584, -11.945, 18.316)]
    propTrack = Sequence(getPropAppearTrack(paper, suit.getRightHand(), posPoints, 0.8, MovieUtil.PNT3_ONE, scaleUpTime=0.5))
    propTrack.append(Wait(1.73))
    hitPoint = __toonFacePoint(toon, parent=battle)
    hitPoint.setX(hitPoint.getX() - 1.4)
    missPoint = __toonGroundPoint(attack, toon, 0.7, parent=battle)
    missPoint.setX(missPoint.getX() - 1.1)
    propTrack.append(getPropThrowTrack(attack, paper, [hitPoint], [missPoint], parent=battle))
    toonTrack = getToonTrack(attack, 3.4, ['conked'], 2.8, ['jump'])
    return Parallel(suitTrack, toonTrack, propTrack)


def doWithdrawal(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    BattleParticles.loadParticles()
    particleEffect = BattleParticles.createParticleEffect('Withdrawal')
    BattleParticles.setEffectTexture(particleEffect, 'snow-particle')
    suitTrack = getSuitAnimTrack(attack)
    partTrack = getPartTrack(particleEffect, 1e-05, suitTrack.getDuration() + 1.2, [particleEffect, suit, 0])
    toonTrack = getToonTrack(attack, 1.2, ['cringe'], 0.2, splicedDodgeAnims=[['duck', 1e-05, 0.8]], showMissedExtraTime=0.8)
    headParts = toon.getHeadParts()
    torsoParts = toon.getTorsoParts()
    legsParts = toon.getLegsParts()

    def changeColor(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(Func(nextPart.setColorScale, Vec4(0, 0, 0, 1)))

        return track

    def resetColor(parts):
        track = Parallel()
        for partNum in range(0, parts.getNumPaths()):
            nextPart = parts.getPath(partNum)
            track.append(Func(nextPart.clearColorScale))

        return track

    soundTrack = getSoundTrack('SA_withdrawl.ogg', delay=1.4, node=suit)
    if dmg > 0:
        colorTrack = Sequence()
        colorTrack.append(Wait(1.6))
        colorTrack.append(Func(battle.movie.needRestoreColor))
        colorTrack.append(Parallel(changeColor(headParts), changeColor(torsoParts), changeColor(legsParts)))
        colorTrack.append(Wait(2.9))
        colorTrack.append(resetColor(headParts))
        colorTrack.append(resetColor(torsoParts))
        colorTrack.append(resetColor(legsParts))
        colorTrack.append(Func(battle.movie.clearRestoreColor))
        return Parallel(suitTrack, partTrack, toonTrack, soundTrack, colorTrack)
    return Parallel(suitTrack, partTrack, toonTrack, soundTrack)


def doJargon(attack):
    suit = attack['suit']
    battle = attack['battle']
    BattleParticles.loadParticles()
    particleEffect = BattleParticles.createParticleEffect(file='jargonSpray')
    particleEffect2 = BattleParticles.createParticleEffect(file='jargonSpray')
    particleEffect3 = BattleParticles.createParticleEffect(file='jargonSpray')
    particleEffect4 = BattleParticles.createParticleEffect(file='jargonSpray')
    BattleParticles.setEffectTexture(particleEffect, 'jargon-brow', color=Vec4(1, 0, 0, 1))
    BattleParticles.setEffectTexture(particleEffect2, 'jargon-deep', color=Vec4(0, 0, 0, 1))
    BattleParticles.setEffectTexture(particleEffect3, 'jargon-hoop', color=Vec4(1, 0, 0, 1))
    BattleParticles.setEffectTexture(particleEffect4, 'jargon-ipo', color=Vec4(0, 0, 0, 1))
    damageDelay = 2.2
    dodgeDelay = 1.5
    partDelay = 1.1
    partInterval = 1.2
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(particleEffect, partDelay + partInterval * 0, 2, [particleEffect, suit, 0])
    partTrack2 = getPartTrack(particleEffect2, partDelay + partInterval * 1, 2, [particleEffect2, suit, 0])
    partTrack3 = getPartTrack(particleEffect3, partDelay + partInterval * 2, 2, [particleEffect3, suit, 0])
    partTrack4 = getPartTrack(particleEffect4, partDelay + partInterval * 3, 1.0, [particleEffect4, suit, 0])
    damageAnims = []
    damageAnims.append(['conked',
     0.0001,
     0,
     0.4])
    damageAnims.append(['conked',
     0.0001,
     2.7,
     0.85])
    damageAnims.append(['conked',
     0.0001,
     0.4,
     0.09])
    damageAnims.append(['conked',
     0.0001,
     0.4,
     0.09])
    damageAnims.append(['conked',
     0.0001,
     0.4,
     0.66])
    damageAnims.append(['conked',
     0.0001,
     0.4,
     0.09])
    damageAnims.append(['conked',
     0.0001,
     0.4,
     0.09])
    damageAnims.append(['conked',
     0.0001,
     0.4,
     0.86])
    damageAnims.append(['conked',
     0.0001,
     0.4,
     0.14])
    damageAnims.append(['conked',
     0.0001,
     0.4,
     0.14])
    damageAnims.append(['conked', 0.0001, 0.4])
    dodgeAnims = [['duck', 0.0001, 1.2], ['duck', 0.0001, 1.3]]
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, splicedDodgeAnims=dodgeAnims, showMissedExtraTime=1.6, showDamageExtraTime=0.7)
    soundTrack = getSoundTrack('SA_jargon.ogg', delay=2.1, node=suit)
    return Parallel(suitTrack, toonTrack, soundTrack, partTrack, partTrack2, partTrack3, partTrack4)


def doMumboJumbo(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    BattleParticles.loadParticles()
    particleEffect = BattleParticles.createParticleEffect(file='mumboJumboSpray')
    particleEffect2 = BattleParticles.createParticleEffect(file='mumboJumboSpray')
    particleEffect3 = BattleParticles.createParticleEffect(file='mumboJumboSmother')
    particleEffect4 = BattleParticles.createParticleEffect(file='mumboJumboSmother')
    particleEffect5 = BattleParticles.createParticleEffect(file='mumboJumboSmother')
    BattleParticles.setEffectTexture(particleEffect, 'mumbojumbo-boiler', color=Vec4(1, 0, 0, 1))
    BattleParticles.setEffectTexture(particleEffect2, 'mumbojumbo-creative', color=Vec4(1, 0, 0, 1))
    BattleParticles.setEffectTexture(particleEffect3, 'mumbojumbo-deben', color=Vec4(1, 0, 0, 1))
    BattleParticles.setEffectTexture(particleEffect4, 'mumbojumbo-high', color=Vec4(1, 0, 0, 1))
    BattleParticles.setEffectTexture(particleEffect5, 'mumbojumbo-iron', color=Vec4(1, 0, 0, 1))
    suitTrack = getSuitTrack(attack)
    partTrack = getPartTrack(particleEffect, 2.5, 2, [particleEffect, suit, 0])
    partTrack2 = getPartTrack(particleEffect2, 2.5, 2, [particleEffect2, suit, 0])
    partTrack3 = getPartTrack(particleEffect3, 3.3, 1.7, [particleEffect3, toon, 0])
    partTrack4 = getPartTrack(particleEffect4, 3.3, 1.7, [particleEffect4, toon, 0])
    partTrack5 = getPartTrack(particleEffect5, 3.3, 1.7, [particleEffect5, toon, 0])
    toonTrack = getToonTrack(attack, 3.2, ['cringe'], 2.2, ['sidestep'])
    soundTrack = getSoundTrack('SA_mumbo_jumbo.ogg', delay=2.5, node=suit)
    if dmg > 0:
        return Parallel(suitTrack, toonTrack, soundTrack, partTrack, partTrack2, partTrack3, partTrack4, partTrack5)
    return Parallel(suitTrack, toonTrack, soundTrack, partTrack, partTrack2)


def doObjection(attack):
    suit = attack['suit']
    battle = attack['battle']
    suitAnims = []
    suitAnims.append(['finger-wag',
     1e-05,
     0,
     0.875])
    suitAnims.append(['finger-wag',
     1e-05,
     2.8,
     0.1])
    suitAnims.append(['finger-wag',
     1,
     2.875])
    suitTrack = getSuitTrack(attack, splicedAnims=suitAnims)
    damageDelay = 0.95
    dodgeDelay = 0.5
    toonTrack = getToonTrack(attack, damageDelay, ['slip-backward'], dodgeDelay, ['sidestep'])
    soundTrack = getSoundTrack('SA_objection.ogg', delay=0.95, node=suit)
    return Parallel(suitTrack, toonTrack, soundTrack)


def doGuiltTrip(attack):
    suit = attack['suit']
    battle = attack['battle']
    centerColor = Vec4(1.0, 0.2, 0.2, 0.9)
    edgeColor = Vec4(0.9, 0.9, 0.9, 0.4)
    powerBar1 = BattleParticles.createParticleEffect(file='guiltTrip')
    powerBar2 = BattleParticles.createParticleEffect(file='guiltTrip')
    powerBar1.setPos(0, 6.1, 0.4)
    powerBar1.setHpr(-90, 0, 0)
    powerBar2.setPos(0, 6.1, 0.4)
    powerBar2.setHpr(90, 0, 0)
    powerBar1.setScale(5)
    powerBar2.setScale(5)
    powerBar1Particles = powerBar1.getParticlesNamed('particles-1')
    powerBar2Particles = powerBar2.getParticlesNamed('particles-1')
    powerBar1Particles.renderer.setCenterColor(centerColor)
    powerBar1Particles.renderer.setEdgeColor(edgeColor)
    powerBar2Particles.renderer.setCenterColor(centerColor)
    powerBar2Particles.renderer.setEdgeColor(edgeColor)
    waterfallEffect = BattleParticles.createParticleEffect('Waterfall')
    waterfallEffect.setScale(11)
    waterfallParticles = waterfallEffect.getParticlesNamed('particles-1')
    waterfallParticles.renderer.setCenterColor(centerColor)
    waterfallParticles.renderer.setEdgeColor(edgeColor)
    suitTrack = getSuitAnimTrack(attack)

    def getPowerTrack(effect, suit=suit, battle=battle):
        partTrack = Sequence(Wait(0.7), Func(battle.movie.needRestoreParticleEffect, effect), Func(effect.start, suit), Wait(0.4), LerpPosInterval(effect, 1.0, Point3(0, 15, 0.4)), LerpFunctionInterval(effect.setAlphaScale, fromData=1, toData=0, duration=0.4), Func(effect.cleanup), Func(battle.movie.clearRestoreParticleEffect, effect))
        return partTrack

    partTrack1 = getPowerTrack(powerBar1)
    partTrack2 = getPowerTrack(powerBar2)
    waterfallTrack = getPartTrack(waterfallEffect, 0.6, 0.6, [waterfallEffect, suit, 0])
    toonTracks = getToonTracks(attack, 1.5, ['slip-forward'], 0.86, ['jump'])
    soundTrack = getSoundTrack('SA_guilt_trip.ogg', delay=1.1, node=suit)
    return Parallel(suitTrack, partTrack1, partTrack2, soundTrack, waterfallTrack, toonTracks)


def doRestrainingOrder(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    paper = globalPropPool.getProp('shredder-paper')
    suitTrack = getSuitTrack(attack)
    posPoints = [Point3(-0.04, 0.15, -1.38), VBase3(10.584, -11.945, 18.316)]
    propTrack = Sequence(getPropAppearTrack(paper, suit.getRightHand(), posPoints, 0.8, MovieUtil.PNT3_ONE, scaleUpTime=0.5))
    propTrack.append(Wait(1.73))
    hitPoint = __toonFacePoint(toon, parent=battle)
    hitPoint.setX(hitPoint.getX() - 1.4)
    missPoint = __toonGroundPoint(attack, toon, 0.7, parent=battle)
    missPoint.setX(missPoint.getX() - 1.1)
    propTrack.append(getPropThrowTrack(attack, paper, [hitPoint], [missPoint], parent=battle))
    damageAnims = [
     ['conked',
      0.01,
      0.3,
      0.2], ['struggle', 0.01, 0.2]]
    toonTrack = getToonTrack(attack, damageDelay=3.4, splicedDamageAnims=damageAnims, dodgeDelay=2.8, dodgeAnimNames=['sidestep'])
    if dmg > 0:
        restraintCloud = BattleParticles.createParticleEffect(file='restrainingOrderCloud')
        restraintCloud.setPos(hitPoint.getX(), hitPoint.getY() + 0.5, hitPoint.getZ())
        cloudTrack = getPartTrack(restraintCloud, 3.5, 0.2, [restraintCloud, battle, 0])
        return Parallel(suitTrack, cloudTrack, toonTrack, propTrack)
    return Parallel(suitTrack, toonTrack, propTrack)


def doSpin(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    damageDelay = 1.7
    sprayEffect = BattleParticles.createParticleEffect(file='spinSpray')
    spinEffect1 = BattleParticles.createParticleEffect(file='spinEffect')
    spinEffect2 = BattleParticles.createParticleEffect(file='spinEffect')
    spinEffect3 = BattleParticles.createParticleEffect(file='spinEffect')
    spinEffect1.reparentTo(toon)
    spinEffect2.reparentTo(toon)
    spinEffect3.reparentTo(toon)
    height1 = toon.getHeight() * (random.random() * 0.2 + 0.7)
    height2 = toon.getHeight() * (random.random() * 0.2 + 0.4)
    height3 = toon.getHeight() * (random.random() * 0.2 + 0.1)
    spinEffect1.setPos(0.8, -0.7, height1)
    spinEffect1.setHpr(0, 0, -random.random() * 10 - 85)
    spinEffect1.setHpr(spinEffect1, 0, 50, 0)
    spinEffect2.setPos(0.8, -0.7, height2)
    spinEffect2.setHpr(0, 0, -random.random() * 10 - 85)
    spinEffect2.setHpr(spinEffect2, 0, 50, 0)
    spinEffect3.setPos(0.8, -0.7, height3)
    spinEffect3.setHpr(0, 0, -random.random() * 10 - 85)
    spinEffect3.setHpr(spinEffect3, 0, 50, 0)
    spinEffect1.wrtReparentTo(battle)
    spinEffect2.wrtReparentTo(battle)
    spinEffect3.wrtReparentTo(battle)
    suitTrack = getSuitTrack(attack)
    sprayTrack = getPartTrack(sprayEffect, 1.0, 1.9, [sprayEffect, suit, 0])
    spinTrack1 = getPartTrack(spinEffect1, 2.1, 3.9, [spinEffect1, battle, 0])
    spinTrack2 = getPartTrack(spinEffect2, 2.1, 3.9, [spinEffect2, battle, 0])
    spinTrack3 = getPartTrack(spinEffect3, 2.1, 3.9, [spinEffect3, battle, 0])
    damageAnims = []
    damageAnims.append(['duck',
     0.01,
     0.01,
     1.1])
    damageAnims.extend(getSplicedLerpAnims('think', 0.66, 1.1, startTime=2.26))
    damageAnims.extend(getSplicedLerpAnims('think', 0.66, 1.1, startTime=2.26))
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=0.91, dodgeAnimNames=['sidestep'], showDamageExtraTime=2.1, showMissedExtraTime=1.0)
    if dmg > 0:
        toonSpinTrack = Sequence(Wait(damageDelay + 0.9), LerpHprInterval(toon, 0.7, Point3(-10, 0, 0)), LerpHprInterval(toon, 0.5, Point3(-30, 0, 0)), LerpHprInterval(toon, 0.2, Point3(-60, 0, 0)), LerpHprInterval(toon, 0.7, Point3(-700, 0, 0)), LerpHprInterval(toon, 1.0, Point3(-1310, 0, 0)), LerpHprInterval(toon, 0.4, toon.getHpr()), Wait(0.5))
        return Parallel(suitTrack, sprayTrack, toonTrack, toonSpinTrack, spinTrack1, spinTrack2, spinTrack3)
    return Parallel(suitTrack, sprayTrack, toonTrack)


def doLegalese(attack):
    suit = attack['suit']
    BattleParticles.loadParticles()
    sprayEffect1 = BattleParticles.createParticleEffect(file='legaleseSpray')
    sprayEffect2 = BattleParticles.createParticleEffect(file='legaleseSpray')
    sprayEffect3 = BattleParticles.createParticleEffect(file='legaleseSpray')
    color = Vec4(0.4, 0, 0, 1)
    BattleParticles.setEffectTexture(sprayEffect1, 'legalese-hc', color=color)
    BattleParticles.setEffectTexture(sprayEffect2, 'legalese-qpq', color=color)
    BattleParticles.setEffectTexture(sprayEffect3, 'legalese-vd', color=color)
    partDelay = 1.3
    partDuration = 1.15
    damageDelay = 1.9
    dodgeDelay = 1.1
    suitTrack = getSuitTrack(attack)
    sprayTrack1 = getPartTrack(sprayEffect1, partDelay, partDuration, [sprayEffect1, suit, 0])
    sprayTrack2 = getPartTrack(sprayEffect2, partDelay + 0.8, partDuration, [sprayEffect2, suit, 0])
    sprayTrack3 = getPartTrack(sprayEffect3, partDelay + 1.6, partDuration, [sprayEffect3, suit, 0])
    damageAnims = []
    damageAnims.append(['cringe',
     1e-05,
     0.3,
     0.8])
    damageAnims.append(['cringe',
     1e-05,
     0.3,
     0.8])
    damageAnims.append(['cringe', 1e-05, 0.3])
    toonTrack = getToonTrack(attack, damageDelay=damageDelay, splicedDamageAnims=damageAnims, dodgeDelay=dodgeDelay, dodgeAnimNames=['sidestep'], showMissedExtraTime=0.8)
    return Parallel(suitTrack, toonTrack, sprayTrack1, sprayTrack2, sprayTrack3)


def doPeckingOrder(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    throwDuration = 3.03
    throwDelay = 3.2
    suitTrack = getSuitTrack(attack)
    numBirds = random.randint(4, 7)
    birdTracks = Parallel()
    propDelay = 1.5
    for i in range(0, numBirds):
        next = globalPropPool.getProp('bird')
        next.setScale(0.01)
        next.reparentTo(suit.getRightHand())
        next.setPos(random.random() * 0.6 - 0.3, random.random() * 0.6 - 0.3, random.random() * 0.6 - 0.3)
        if dmg > 0:
            hitPoint = Point3(random.random() * 5 - 2.5, random.random() * 2 - 1 - 6, random.random() * 3 - 1.5 + toon.getHeight() - 0.9)
        else:
            hitPoint = Point3(random.random() * 2 - 1, random.random() * 4 - 2 - 15, random.random() * 4 - 2 + 2.2)
        birdTrack = Sequence(Wait(throwDelay), Func(battle.movie.needRestoreRenderProp, next), Func(next.wrtReparentTo, battle), Func(next.setHpr, Point3(90, 20, 0)), LerpPosInterval(next, 1.1, hitPoint))
        scaleTrack = Sequence(Wait(throwDelay), LerpScaleInterval(next, 0.15, Point3(9, 9, 9)))
        birdTracks.append(Sequence(Parallel(birdTrack, scaleTrack), Func(MovieUtil.removeProp, next)))

    damageAnims = []
    damageAnims.append(['cringe',
     0.01,
     0.14,
     0.21])
    damageAnims.append(['cringe',
     0.01,
     0.14,
     0.13])
    damageAnims.append(['cringe', 0.01, 0.43])
    toonTrack = getToonTrack(attack, damageDelay=4.2, splicedDamageAnims=damageAnims, dodgeDelay=2.8, dodgeAnimNames=['sidestep'], showMissedExtraTime=1.1)
    return Parallel(suitTrack, toonTrack, birdTracks)


def doJumpAttack(attack):
    suit = attack['suit']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])
    suitTrack = Parallel(Sequence(Parallel(SoundInterval(suit.suitBoss.upSfx, node=suit.suitBoss), ActorInterval(suit.suitBoss, 'Fb_down2Up')), Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), ActorInterval(suit.suitBoss, 'Fb_jump'), Parallel(ActorInterval(suit.suitBoss, 'Fb_down2Up', playRate=-1), SoundInterval(suit.suitBoss.downSfx, node=suit.suitBoss)), Func(suit.clearChat), Func(suit.suitBoss.loop, 'Fb_downNeutral')), Sequence(Wait(2.5), SoundInterval(suit.suitBoss.swishSfx, duration=1.1), SoundInterval(suit.suitBoss.boomSfx, duration=1.9)))
    toonTracks = getToonTracks(attack, 3.7, ['slip-forward'], 3.0, ['jump'])
    return Parallel(suitTrack, toonTracks)


def doGearThrowAttack(attack):
    suit = attack['suit']
    target = attack['target']
    toon = target['toon']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])
    gearRoot = suit.suitBoss.rotateNode.attachNewNode('gearRoot')
    gearRoot.setZ(10)
    gearModel = loader.loadModel('phase_9/models/char/gearProp')
    gearModel.setScale(0.2)
    gearRoot.headsUp(toon)
    toToonH = PythonUtil.fitDestAngle2Src(0, gearRoot.getH() + 180)
    gearRoot.lookAt(toon)
    gearTrack = Parallel()
    for i in range(4):
        node = gearRoot.attachNewNode(str(i))
        node.hide()
        node.setPos(0, 5.85, 4.0)
        gear = gearModel.instanceTo(node)
        x = random.uniform(-5, 5)
        z = random.uniform(-3, 3)
        h = random.uniform(-720, 720)
        gearTrack.append(Sequence(Wait(i * 0.15), Func(node.show), Parallel(node.posInterval(1, Point3(x, 50, z), fluid=1), node.hprInterval(1, VBase3(h, 0, 0), fluid=1)), Func(node.detachNode)))

    suitTrack = Sequence(Parallel(SoundInterval(suit.suitBoss.upSfx, node=suit.suitBoss), ActorInterval(suit.suitBoss, 'Fb_down2Up'), Sequence(Wait(1), suit.suitBoss.pelvis.hprInterval(1, VBase3(toToonH, 0, 0)))), Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), Parallel(Sequence(Wait(0.19), gearTrack, Func(gearRoot.detachNode)), SoundInterval(suit.suitBoss.throwSfx, node=suit.suitBoss), Sequence(ActorInterval(suit.suitBoss, 'Fb_UpThrow'), Parallel(Sequence(ActorInterval(suit.suitBoss, 'Fb_down2Up', playRate=-1), Func(suit.clearChat), Func(suit.suitBoss.loop, 'Fb_downNeutral')), SoundInterval(suit.suitBoss.downSfx, node=suit.suitBoss), Sequence(Wait(0.69), suit.suitBoss.pelvis.hprInterval(0.69, VBase3(0, 0, 0)))))))
    toonTrack = getToonTrack(attack, 3.35, ['slip-backward'], 2.8, ['sidestep'])
    return Parallel(suitTrack, toonTrack)


def doGearStormAttack(attack):
    suit = attack['suit']
    targets = attack['target']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])
    largeAttackSfx = loader.loadSfx('phase_5/audio/sfx/SA_brainstorm.ogg')
    suitTrack = Parallel()
    for t in targets:
        toon = t['toon']
        stormcloud = loader.loadModel('phase_4/models/props/stormcloud-mod')
        stormcloud.reparentTo(suit.suitBoss)
        stormcloud.setScale(0)
        stormcloud.setZ(2.5)
        gears = BattleParticles.loadParticleFile('gearRain.ptf')
        gears.setDepthWrite(False)
        openSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_door_open.ogg')
        closeSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_door_close.ogg')
        openedHpr = (-90, 0, 80)
        closedHpr = (-90, 0, 0)
        suitTrack.append(Sequence(Parallel(SoundInterval(suit.suitBoss.upSfx, node=suit.suitBoss), ActorInterval(suit.suitBoss, 'Fb_down2Up')), Parallel(Sequence(Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), ActorInterval(suit.suitBoss, 'Bb_point'), Func(suit.suitBoss.loop, 'Fb_neutral')), Sequence(Parallel(Sequence(Parallel(SoundInterval(openSfx, node=suit.suitBoss, volume=0.2), suit.suitBoss.find('**/joint_doorFront').hprInterval(1, openedHpr, blendType='easeInOut')), Parallel(suit.suitBoss.find('**/joint_doorFront').hprInterval(1, closedHpr, blendType='easeInOut'), SoundInterval(closeSfx, node=suit.suitBoss, volume=0.2))), LerpPosInterval(stormcloud, duration=2, pos=(0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  -17,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  7)), Sequence(stormcloud.scaleInterval(2, (7.5,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             7.5,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             5.5)), Parallel(Func(stormcloud.wrtReparentTo, render), Sequence(stormcloud.posInterval(2, (toon.getX(), toon.getY(), 10), blendType='easeOut'), Parallel(Func(suit.clearChat), Func(base.playSfx, largeAttackSfx), ParticleInterval(gears, stormcloud, worldRelative=0, duration=1.5, cleanup=True)), stormcloud.scaleInterval(1, (0.0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 0.0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 0.0))), Sequence(Parallel(Sequence(Wait(1), Parallel(ActorInterval(suit.suitBoss, 'Fb_down2Up', playRate=-1), SoundInterval(suit.suitBoss.downSfx, node=suit.suitBoss)))), Func(suit.suitBoss.loop, 'Fb_downNeutral'))))))), Func(stormcloud.removeNode)))

    damageAnims = [
     [
      'cringe', 0.01, 0.4, 0.8], ['duck', 1e-06, 1.6]]
    toonTracks = getToonTracks(attack, damageDelay=6.5, splicedDamageAnims=damageAnims, dodgeDelay=6.0, dodgeAnimNames=[
     'sidestep'], showMissedExtraTime=1.1)
    return Parallel(suitTrack, toonTracks)


def doCanAttackAttack(attack):
    suit = attack['suit']
    target = attack['target']
    toon = target['toon']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])
    can = loader.loadModel('phase_12/models/bossbotHQ/canoffood').find('**/can')
    can.setPosHprScale(-2.5, 0.4374, 1.9499, 0.0, 0.0, 90.0, 2.5, 2.5, 2.5)
    can.reparentTo(suit.suitBoss)
    damageShow = can.attachNewNode('damageShowNode')
    match = loader.loadModel('phase_14/models/props/fire-match')
    match.setScale(4)
    match.hide()
    match.setPosHpr(0.7262, -0.004, -0.589, -178, -89.0, 0.0)
    match.reparentTo(suit.suitBoss.find('**/joint17'))
    fire = BattleParticles.loadParticleFile('firedFlame.ptf')
    fire.setScale(0.35)
    explode = loader.loadModel('phase_3.5/models/props/explosion')
    explode.setBillboardAxis()
    explode.setScale(0.75)
    explode.hide()
    explode.reparentTo(can)
    h = random.uniform(-720, 720)
    canThrow = Parallel(can.posInterval(0.5, Point3(toon.getX(render), toon.getY(render), 0.5), fluid=1), can.hprInterval(0.5, VBase3(h, 0, 0), fluid=1), Sequence(Wait(0.4), Func(explode.wrtReparentTo, render), Func(explode.setHpr, 0, 0, 0), Func(explode.show), Func(base.playSfx, suit.suitBoss.boomSfx, node=explode), LerpScaleInterval(damageShow, scale=Point3(5.0, 5.0, 5.0), duration=0.1)))
    openSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_door_open.ogg')
    closeSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_door_close.ogg')
    openedHpr = (-90, 0, 80)
    closedHpr = (-90, 0, 0)
    canTrack = Sequence(Parallel(SoundInterval(openSfx, node=suit.suitBoss, volume=0.2, duration=1.5), Sequence(suit.suitBoss.find('**/joint_doorFront').hprInterval(1, openedHpr, blendType='easeInOut'), suit.suitBoss.find('**/joint_doorFront').hprInterval(0.5, openedHpr, blendType='easeInOut')), can.posHprInterval(1.5, (-2.5,
                                                                                                                                                                                                                                                                                                                                  -10.812,
                                                                                                                                                                                                                                                                                                                                  2.0474), (0.0,
                                                                                                                                                                                                                                                                                                                                            545,
                                                                                                                                                                                                                                                                                                                                            90.0))), Parallel(ProjectileInterval(can, endPos=(0.2199,
                                                                                                                                                                                                                                                                                                                                                                                              -7.8767,
                                                                                                                                                                                                                                                                                                                                                                                              10.75), duration=1.5, gravityMult=2.5), can.hprInterval(1.5, (171.0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                            561,
                                                                                                                                                                                                                                                                                                                                                                                                                                                            538.0)), SoundInterval(closeSfx, node=suit.suitBoss, volume=0.2, duration=1.5), suit.suitBoss.find('**/joint_doorFront').hprInterval(1, closedHpr, blendType='easeInOut')), Func(can.wrtReparentTo, suit.suitBoss.find('**/joint54')), Wait(3.0), Func(match.show), Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), Wait(1.0), Func(fire.start, parent=match), Wait(2.0), can.colorScaleInterval(1.0, (1,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            0)), Func(match.removeNode), Wait(1.2), Func(suit.clearChat), Func(can.wrtReparentTo, render), canThrow, Func(can.detachNode), Wait(0.3), Func(explode.removeNode))
    bossTrack = Sequence(Wait(1.9), Func(suit.suitBoss.forwardHead), ActorInterval(suit.suitBoss, 'canAttack'), Func(suit.suitBoss.reverseHead), Func(suit.suitBoss.loop, 'Fb_downNeutral'))
    suitTrack = Parallel(bossTrack, canTrack)
    toonTrack = getToonTrack(attack, 11.75, ['slip-backward'], 11.25, ['sidestep'])
    return Parallel(suitTrack, toonTrack)


def doSafeThrowAttack(attack):
    suit = attack['suit']
    target = attack['target']
    dmg = target['hp']
    toon = target['toon']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])
    safe = loader.loadModel('phase_10/models/cashbotHQ/CashBotSafe')
    safe.setHpr(180, 0, 180)
    safe.setPos(0.8, 0, 0.9)
    safe.setScale(0.01)
    safe.find('**/SafeShadow1').hide()
    safe.reparentTo(suit.suitBoss.find('**/joint17'))
    appearSfx = loader.loadSfx('phase_5/audio/sfx/SA_watercooler_appear_only.ogg')
    throwSfx = loader.loadSfx('phase_5/audio/sfx/SA_hardball_impact_only.ogg')
    landSfx = loader.loadSfx('phase_5/audio/sfx/AA_drop_bigweight_miss.ogg')
    landSfx.setVolume(0.42)
    toonScale = toon.find('**/actorGeom').getScale()
    if dmg > 0:
        squishTrack = toon.find('**/actorGeom').scaleInterval(0.05, (1, 1, 0.01))
    else:
        squishTrack = toon.find('**/actorGeom').scaleInterval(0.05, toonScale)
    suitTrack = Parallel(Sequence(Func(suit.suitBoss.find('**/joint_lifeMeter').hide), ActorInterval(suit.suitBoss, 'Fb_safe-throw'), Func(suit.suitBoss.loop, 'Fb_downNeutral'), Func(suit.suitBoss.find('**/joint_lifeMeter').show)), Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), Sequence(Wait(1.1), Parallel(safe.scaleInterval(0.25, (0.38,
                                                                                                                                                                                                                                                                                                                                                        0.38,
                                                                                                                                                                                                                                                                                                                                                        0.38)), SoundInterval(appearSfx, duration=0.25)), Wait(2.3), Func(safe.wrtReparentTo, render), Parallel(safe.hprInterval(0.9, (0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       360,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       0)), SoundInterval(throwSfx, duration=0.7), ProjectileInterval(safe, duration=0.9, endPos=toon.getPos(), gravityMult=5.0), Sequence(Wait(0.85), Func(landSfx.play), Func(safe.find('**/SafeShadow1').show), squishTrack)), Func(safe.wrtReparentTo, toon), safe.posInterval(0.69, (safe.getX(), safe.getY() - 10, 0), blendType='easeOut'), Func(suit.clearChat), Wait(0.25), Func(safe.wrtReparentTo, render), Parallel(Sequence(safe.scaleInterval(0.5, (0.01,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  0.01,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  0.01)), Func(safe.removeNode)), toon.find('**/actorGeom').scaleInterval(0.5, toonScale))))
    toonTrack = getToonTrack(attack, 5.0, ['jump'], 3.75, ['sidestep'])
    return Parallel(suitTrack, toonTrack)


def doCashTornadoAttack(attack):
    suit = attack['suit']
    target = attack['target']
    battle = attack['battle']
    toon = target['toon']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])

    def doMoneyTornadoAttack():
        whirlSfx = loader.loadSfx('phase_5/audio/sfx/tt_s_ara_cfg_whirlwind.ogg')
        tornadoNode = NodePath('tornadoNode')
        tornadoNode.reparentTo(battle)
        tornadoNode.setPos(0, 3, 1)
        tornadoNode.setScale(0.2)
        whirlSfx.setLoop(True)
        whirlSfx.play()
        for x in range(40):
            tornadoNode.attachNewNode('billNode' + str(x))
            bill = loader.loadModel('phase_10/models/cashbotHQ/MoneyStack')
            bill.setTwoSided(True)
            bill.setPosHprScale(0, 0, 0, random.randint(0, 360), 0, random.randint(0, 360), 3.0 - x * 0.03, 3.0 - x * 0.03, 3.0 - x * 0.03)
            bill.reparentTo(tornadoNode.find('**/billNode' + str(x)))
            bill.hide()
            originalBillZ = tornadoNode.find('**/billNode' + str(x)).getZ()
            originalBillH = bill.getH()
            originalBillR = bill.getR()
            seq = Sequence(Parallel(Sequence(tornadoNode.find('**/billNode' + str(x)).posInterval(0.5, (0, 0, random.randint(-10, 10))), tornadoNode.find('**/billNode' + str(x)).posInterval(0.5, (0, 0, originalBillZ))), Sequence(bill.hprInterval(0.5, (random.randint(-360, 360), 0, random.randint(-360, 360))), bill.hprInterval(0.5, (originalBillH, 0, originalBillR))), tornadoNode.find('**/billNode' + str(x)).hprInterval(1, (-360,
                                                                                                                                                                                                                                                                                                                                                                                                                                           0,
                                                                                                                                                                                                                                                                                                                                                                                                                                           0))))
            whirlSeq = Sequence(Wait(x * 0.1), Func(bill.show), Func(seq.loop), bill.posInterval(0.5, (30 - x / 2, 0, 75 - x ** 1.3)), Wait(2.0), Func(bill.removeNode))
            whirlSeq.start()

        Parallel(Sequence(Wait(1.75), Func(tornadoNode.wrtReparentTo, render), tornadoNode.posInterval(1.0, toon.getPos()), Wait(2.55), Func(whirlSfx.stop), Func(tornadoNode.removeNode))).start()

    suitTrack = Sequence(Parallel(SoundInterval(suit.suitBoss.upSfx, node=suit.suitBoss), ActorInterval(suit.suitBoss, 'Fb_down2Up')), Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), Func(doMoneyTornadoAttack), ActorInterval(suit.suitBoss, 'Bb_point'), Parallel(Sequence(ActorInterval(suit.suitBoss, 'Fb_down2Up', playRate=-1), Func(suit.clearChat), Func(suit.suitBoss.loop, 'Fb_downNeutral')), SoundInterval(suit.suitBoss.downSfx, node=suit.suitBoss)))
    toonTrack = getToonTrack(attack, 5.25, ['slip-forward'], 4.75, ['sidestep'])
    return Parallel(suitTrack, toonTrack)


def doGavelAttack(attack):
    suit = attack['suit']
    battle = attack['battle']
    target = attack['target']
    dmg = target['hp']
    toon = target['toon']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])
    gavel = loader.loadModel('phase_11/models/lawbotHQ/LB_gavel')
    gavel.setPos(0, 10, -20)
    gavel.setScale(2.0)
    gavel.headsUp(toon)
    gavel.setH(gavel.getH() - 93)
    gavel.hide()
    gavel.reparentTo(battle)
    gavelSfx = loader.loadSfx('phase_11/audio/sfx/LB_gavel.ogg')
    toonScale = toon.find('**/actorGeom').getScale()
    if dmg > 0:
        squishTrack = toon.find('**/actorGeom').scaleInterval(0.1, (1, 1, 0.01))
    else:
        squishTrack = toon.find('**/actorGeom').scaleInterval(0.1, toonScale)
    suitTrack = Sequence(Parallel(SoundInterval(suit.suitBoss.upSfx, node=suit.suitBoss), Sequence(ActorInterval(suit.suitBoss, 'Fb_down2Up'), Parallel(Sequence(Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), Func(gavel.show), gavel.posInterval(1.5, (0,
                                                                                                                                                                                                                                                                    10,
                                                                                                                                                                                                                                                                    0), blendType='easeOut'), Parallel(Sequence(gavel.hprInterval(1, (gavel.getH(), 80, gavel.getR()), blendType='easeIn'), Func(gavelSfx.play)), Sequence(Wait(0.9), squishTrack, Wait(1.0), gavel.scaleInterval(1, (0.01,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      0.01,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      0.01)), Func(gavel.removeNode), toon.find('**/actorGeom').scaleInterval(0.2, toonScale)))), Sequence(ActorInterval(suit.suitBoss, 'Bb_point'), Parallel(Sequence(ActorInterval(suit.suitBoss, 'Fb_down2Up', playRate=-1), Func(suit.suitBoss.loop, 'Fb_downNeutral'), Func(suit.clearChat)), SoundInterval(suit.suitBoss.downSfx, node=suit.suitBoss)))))))
    toonTrack = getToonTrack(attack, 6.6, ['jump'], 4.0, ['sidestep'])
    return Parallel(suitTrack, toonTrack)


def doBookshelfAttack(attack):
    targets = attack['target']
    suit = attack['suit']
    battle = attack['battle']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])
    bookshelf = Actor('phase_14/models/props/LB_AttackShelf-mod.bam', {'into-throw': 'phase_14/models/props/LB_AttackShelf-into-throw.bam', 
       'forward-throw': 'phase_14/models/props/LB_AttackShelf-forward-throw.bam', 
       'into-neutral': 'phase_14/models/props/LB_AttackShelf-into-neutral.bam', 
       'walk': 'phase_14/models/props/LB_AttackShelf-walk.bam'})
    bookshelf.setScale(0.1)
    bookshelf.setBlend(frameBlend=True)
    bookshelf.loop('walk')
    bookshelf.setPlayRate(2.5, 'walk')
    bookshelf.reparentTo(suit.suitBoss)
    bookshelf.headsUp(battle)
    openSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_door_open.ogg')
    closeSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_door_close.ogg')
    openedHpr = (-90, 0, 80)
    closedHpr = (-90, 0, 0)
    throwSfx = loader.loadSfx('phase_5/audio/sfx/SA_hardball_impact_only.ogg')
    throwSfx.setVolume(0.25)

    def throwBook(attack, targets, bookshelf, throwSfx=None, end=False):
        if end:
            neutralTrack = Parallel()
            for toon in targets:
                toon = toon['toon']
                neutralTrack.append(Func(toon.loop, 'neutral'))

            throwTrack = Parallel(getToonTracks(attack, damageDelay=0, dodgeDelay=0, splicedDamageAnims=[['slip-backward', 0, 0.85]], splicedDodgeAnims=[
             [
              'duck', 0, 1.7]], hideDmg=True), neutralTrack)
            return throwTrack
        throwTrack = Parallel(getToonTracks(attack, damageDelay=0.4, dodgeDelay=0, splicedDamageAnims=[['slip-backward', 0, 0, 0.45]], splicedDodgeAnims=[
         [
          'duck', 0, 1, 0.85]], splitTripleDmg=True))
        x = -1.5
        for toon in targets:
            toon = toon['toon']
            book = loader.loadModel('phase_14/models/props/lawbot-book')
            book.setPos(x, 0, 3)
            book.hide()
            book.reparentTo(bookshelf)
            x += 1
            throwTrack.append(Sequence(Parallel(Sequence(Wait(0.1), SoundInterval(throwSfx, duration=0.6)), Sequence(Wait(0.2), Func(book.show), Func(book.wrtReparentTo, render), book.posHprInterval(0.5, (toon.getX(), toon.getY(), 4), (0,
                                                                                                                                                                                                                                            720,
                                                                                                                                                                                                                                            0)))), Func(book.removeNode)))

        return throwTrack

    suitTrack = Sequence(Func(bookshelf.setH, bookshelf.getH() + 180), Func(bookshelf.wrtReparentTo, battle), Parallel(SoundInterval(openSfx, node=suit.suitBoss, volume=0.2, duration=1.5), Sequence(Wait(0.75), bookshelf.scaleInterval(0.75, (0.9,
                                                                                                                                                                                                                                                 0.9,
                                                                                                                                                                                                                                                 0.9))), Sequence(suit.suitBoss.find('**/joint_doorFront').hprInterval(1, openedHpr, blendType='easeInOut'), suit.suitBoss.find('**/joint_doorFront').hprInterval(0.5, openedHpr, blendType='easeInOut'), Parallel(SoundInterval(closeSfx, node=suit.suitBoss, volume=0.2, duration=1.5), suit.suitBoss.find('**/joint_doorFront').hprInterval(1, closedHpr, blendType='easeInOut'), Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout))), Sequence(Wait(0.3), bookshelf.posInterval(1.5, (0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                5,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                0)), bookshelf.hprInterval(0.2, (0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 0)), ActorInterval(bookshelf, 'into-throw'), Parallel(throwBook(attack, targets, bookshelf, throwSfx), ActorInterval(bookshelf, 'forward-throw')), Parallel(throwBook(attack, targets, bookshelf, throwSfx), ActorInterval(bookshelf, 'forward-throw')), Parallel(throwBook(attack, targets, bookshelf, throwSfx), ActorInterval(bookshelf, 'forward-throw')), Parallel(throwBook(attack, targets, bookshelf, end=True), Sequence(Func(suit.clearChat), ActorInterval(bookshelf, 'into-neutral'), Func(bookshelf.loop, 'walk'), Func(bookshelf.wrtReparentTo, suit.suitBoss), bookshelf.hprInterval(0.5, (180,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           0)))), Parallel(Sequence(bookshelf.posInterval(1.5, (0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                0)), Func(bookshelf.delete)), Sequence(suit.suitBoss.find('**/joint_doorFront').hprInterval(0.75, openedHpr, blendType='easeInOut'), suit.suitBoss.find('**/joint_doorFront').hprInterval(0.75, openedHpr, blendType='easeInOut')), SoundInterval(openSfx, node=suit.suitBoss, volume=0.2, duration=1.5), bookshelf.scaleInterval(1.2, (0.3,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        0.3,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        0.3))), Parallel(SoundInterval(closeSfx, node=suit.suitBoss, volume=0.2, duration=1.5), suit.suitBoss.find('**/joint_doorFront').hprInterval(1, closedHpr, blendType='easeInOut')))))
    return Parallel(suitTrack)


def doForeAttack(attack):
    suit = attack['suit']
    targets = attack['target']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])
    if not suit.suitBoss.bossClub:
        suit.suitBoss.bossClub = loader.loadModel('phase_12/models/char/bossbotBoss-golfclub')
        suit.suitBoss.bossClub.reparentTo(suit.suitBoss.find('**/joint17'))
        suit.suitBoss.bossClub.setScale(0.01)

    def getGolfBall():
        golfRoot = NodePath('golfRoot')
        golfBall = loader.loadModel('phase_6/models/golf/golf_ball.bam')
        golfBall.setColorScale(0.75, 0.75, 0.75, 0.5)
        golfBall.setTransparency(1)
        ballScale = 5
        golfBall.setScale(ballScale)
        golfBall.reparentTo(golfRoot)
        return golfRoot

    def doGolfAttack(self, toon):
        clubSfx = loader.loadSfx('phase_5/audio/sfx/SA_hardball.ogg')
        distance = toon.getDistance(self)
        gearRoot = self.suitBoss.attachNewNode('gearRoot')
        gearRoot.setZ(10)
        gearModel = getGolfBall()
        self.ballLaunch = NodePath('')
        self.ballLaunch.reparentTo(self.suitBoss)
        self.ballLaunch.setPos(-10.5, -8.5, 5)
        self.ballLaunch.lookAt(toon)
        gearRoot.headsUp(toon)
        toToonH = PythonUtil.fitDestAngle2Src(0, gearRoot.getH() + 180)
        gearRoot.lookAt(toon)
        gearTrack = Parallel()
        for i in range(5):
            node = gearRoot.attachNewNode('node')
            node.hide()
            node.reparentTo(self.ballLaunch)
            distance = toon.getDistance(node)
            gearModel.instanceTo(node)
            x = random.uniform(-5, 5)
            z = random.uniform(-3, 3)
            p = random.uniform(-720, -90)
            y = distance + random.uniform(5, 15)
            if i == 2:
                x = 0
                z = 0
                y = distance + 10

            def detachNode(node):
                if not node.isEmpty():
                    node.detachNode()
                return Task.done

            def detachNodeLater(node=node):
                if node.isEmpty():
                    return
                node.node().setBounds(BoundingSphere(Point3(0, 0, 0), distance * 1.5))
                node.node().setFinal(1)
                taskMgr.doMethodLater(0.005, detachNode, 'detach-%s-%s' % (gearRoot.getName(), node.getName()), extraArgs=[
                 node])

            gearTrack.append(Sequence(Wait(26.0 / 24.0), Wait(i * 0.15), Func(node.show), Parallel(node.posInterval(1, Point3(x, y, z), fluid=1), node.hprInterval(1, VBase3(0, p, 0), fluid=1)), Func(detachNodeLater)))

        seq = Sequence(Parallel(Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), Func(self.suitBoss.getPart('torso').setHpr, 0, 0, 0), Sequence(Wait(1.55), suit.suitBoss.bossClub.scaleInterval(1.0, (1,
                                                                                                                                                                                                               1,
                                                                                                                                                                                                               1)))), Parallel(Sequence(self.suitBoss.getPart('torso').hprInterval(2, VBase3(1440, 0, 0))), gearTrack, ActorInterval(self.suitBoss, 'golf_swing'), Sequence(Wait(0.75), SoundInterval(clubSfx, duration=0.4)), Sequence(Wait(2.0), Func(suit.clearChat), Parallel(suit.suitBoss.bossClub.scaleInterval(1.0, (0.01,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             0.01,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             0.01)), ActorInterval(suit.suitBoss, 'Fb_down2Up', playRate=-1), SoundInterval(suit.suitBoss.downSfx, node=suit.suitBoss)), Func(suit.suitBoss.loop, 'Fb_downNeutral'), Func(self.suitBoss.getPart('torso').setHpr, 0, 0, 0))))
        return seq

    golfTrack = Parallel()
    for toon in targets:
        golfTrack.append(doGolfAttack(suit, toon['toon']))

    suitTrack = Parallel(SoundInterval(suit.suitBoss.upSfx, node=suit.suitBoss), ActorInterval(suit.suitBoss, 'Fb_down2Up'), golfTrack)
    toonTrack = getToonTracks(attack, 4.3, ['slip-backward'], 3.42, ['sidestep'])
    return Parallel(suitTrack, toonTrack)


def doBossDemotionAttack(attack):
    suit = attack['suit']
    target = attack['target']
    toon = target['toon']
    dmg = target['hp']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])
    poof = loader.loadModel('phase_3.5/models/props/dust_cloud.bam')
    poof.hide()
    poof.setZ(3)
    poof.setBillboardPointEye()
    poof.reparentTo(toon)
    returnSfx = loader.loadSfx('phase_3/audio/sfx/GUI_balloon_popup.ogg')
    demoteSfx = loader.loadSfx('phase_5/audio/sfx/SA_paradigm_shift.ogg')

    def hideNode(toon, node, hide=True):
        for node in toon.findAllMatches('**/%s' % node):
            if hide:
                node.hide()
            else:
                node.show()

    legPart = 'legs'
    pantsPart = '__Actor_torso'
    torsoParts = ['torso-top', 'sleeves', 'arms', 'hands', 'neck']
    headPart = '__Actor_head'
    torsoHideTrack = Sequence()
    for part in torsoParts:
        torsoHideTrack.append(Func(hideNode, toon, part))

    torsoAppearTrack = Sequence(Func(returnSfx.play))
    for part in torsoParts:
        torsoHideTrack.append(Func(hideNode, toon, part, hide=False))

    if dmg > 0:
        attackTrack = Sequence(Func(poof.wrtReparentTo, render), Func(poof.show), Func(hideNode, toon, legPart), Func(hideNode, toon, pantsPart), torsoHideTrack, Func(hideNode, toon, headPart), Wait(0.5), Func(poof.removeNode), Wait(2.25), Func(returnSfx.play), Func(hideNode, toon, legPart, hide=False), Wait(0.1), Func(returnSfx.play), Func(hideNode, toon, pantsPart, hide=False), Wait(0.1), torsoAppearTrack, Func(returnSfx.play), Func(hideNode, toon, headPart, hide=False))
    else:
        attackTrack = Wait(3.0)
        poof.removeNode()
    suitTrack = Sequence(Parallel(SoundInterval(suit.suitBoss.upSfx, node=suit.suitBoss), ActorInterval(suit.suitBoss, 'Fb_down2Up')), Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), Parallel(Sequence(ActorInterval(suit.suitBoss, 'Bb_point'), Func(suit.clearChat), Parallel(Sequence(ActorInterval(suit.suitBoss, 'Fb_down2Up', playRate=-1), Func(suit.suitBoss.loop, 'Fb_downNeutral')), SoundInterval(suit.suitBoss.downSfx, node=suit.suitBoss))), Sequence(Wait(1.42), SoundInterval(demoteSfx, startTime=2.435, duration=1.0)), Sequence(Wait(1.35), attackTrack)))
    toonTrack = getToonTrack(attack, 2.9, ['duck'], 3.25, ['sidestep'])
    return Parallel(suitTrack, toonTrack)


def doReorganizeAttack(attack):
    suit = attack['suit']
    taunt = getAttackTaunt(attack['name'], attack['taunt'])
    suitTrack = Sequence(Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout), Wait(3.0), Func(suit.clearChat))
    return Parallel(suitTrack)