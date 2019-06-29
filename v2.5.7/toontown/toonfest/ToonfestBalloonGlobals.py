from random import choice
from direct.interval.IntervalGlobal import *
from panda3d.core import *
from otp.nametag.NametagConstants import *
BalloonBasePosition = [
 302, -256, 29]
BalloonScale = 1.2
AlecSpeech1 = [
 'Heeeeellllllooooo!',
 'Despite my serendipitous exclamation, I must inform you that I am actually quite terrified!',
 "Balloon rides aren't really my forte. I'm all about voting.",
 'Preferably votes that stay on the ground.',
 'You know, I could have been a Fisherman too. Great scenery. Slimey fish.',
 "On second thought, I couldn't handle fishing. Slime doesn't work well with my gloves.",
 'If they had an official ToonFest counter though? Oh man, that would be the dream.',
 "But no, instead I'm up here in the balloon.",
 "That's the last time I put my name into a ballot! No, just kidding. I love ballots.",
 "Just press the ToonFest Teleport Button when you're ready to come back down!"]
AlecSpeech2 = [
 'Another balloon ride. Just what my day needed!',
 'That was complete sarcasm, too. I actually have a mortal fear of heights.',
 "I've been living my nightmares all day today!",
 "I must say though, this ride isn't so bad yet. At least I'm not alone!",
 'You can see a lot from up here, actually. The mine, the mountains -- is that... Bossbot Castle?',
 'Those Cogs, impeding on even Toonfest! The nerve of those robots.',
 'Just another reason to ramp up the activites each year, I guess.',
 "I'm actually pretty excited to head down now tha--",
 "Hang on - you're getting off here? No, you can't just leave me all the way up here!",
 "Just press the ToonFest Teleport Button when you're ready to come back down. Don't mind me, I'll just float here panicking!"]
AlecSpeech3 = [
 'Need a lift?',
 "I actually wouldn't recommend it.",
 'Say, do you know how many Toons go sad from balloon crashes each year?',
 "One. There's actually only been one and he didn't really go sad from a crash.",
 'He worked with balloons though. So that counts.',
 "I've happened to notice that you haven't asked me to take you back down to the ground yet!",
 "I mean seriously, I'm telling you straightforward: We're not going to survive this ride.",
 "Listen, I didn't want to do this, but we're too high. This is just too high. For your own safety I'm taking us back--",
 "Oh we're here. You know, that was just as bad as anticipated, and now I get to relive it all again. Hooray!",
 "Just press the ToonFest Teleport Button when you're ready to come back down!"]
AlecSpeech4 = [
 'No, no! Blargghh, not another one!',
 "I don't mean to offend very much -- I'm just not a fan of rides.",
 '...or balloons...',
 '...or...heights...',
 'AHH! -- Sorry, just looked down.',
 "I didn't really volunteer for the job you see, it's just that...",
 'Well, you know what happened.',
 'Flippy insisted on having a balloon here in his memory.',
 "Oh boy, we're here. Looks like I get to go back down.",
 "Just click on the ToonFest Teleport Button when you're ready to come back down!"]
AlecSpeechChoices = [
 AlecSpeech1, AlecSpeech2, AlecSpeech3, AlecSpeech4]
AlecSpeeches = choice(AlecSpeechChoices)
NumBalloonPaths = 1

def generateFlightPaths(balloon):
    flightPaths = []
    flightPaths.append(Sequence(Wait(0.5), balloon.balloon.posHprInterval(1.5, Point3(239, -251, 31), (0,
                                                                                                       2,
                                                                                                       2)), balloon.balloon.posHprInterval(1.5, Point3(252, -251, 33), (0,
                                                                                                                                                                        -2,
                                                                                                                                                                        -2)), balloon.balloon.posHprInterval(8.0, Point3(258, -159, 43), (0,
                                                                                                                                                                                                                                          0,
                                                                                                                                                                                                                                          0)), balloon.balloon.posHprInterval(6.5, Point3(250, -140, 76), (5,
                                                                                                                                                                                                                                                                                                           2,
                                                                                                                                                                                                                                                                                                           2)), balloon.balloon.posHprInterval(7.0, Point3(182.88, -135.4, 78.686), (-26.0,
                                                                                                                                                                                                                                                                                                                                                                                     2.0,
                                                                                                                                                                                                                                                                                                                                                                                     2.0)), balloon.balloon.posHprInterval(4.0, Point3(124.97, -82.71, 94.949), (-26.0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                 2.0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                 2.0)), balloon.balloon.posHprInterval(5.5, Point3(187.85, 34.398, 102.08), (175,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             -4,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             0)), balloon.balloon.posHprInterval(10.0, Point3(280, 20, 101), (0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              2,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              -2)), balloon.balloon.posHprInterval(4.5, Point3(300, -32, 104), (-2,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                -2,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                2)), balloon.balloon.posHprInterval(5, Point3(307, -100, 112), (-2,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                -2,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                2)), balloon.balloon.posHprInterval(5, Point3(320, -168, 112), (-2,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                -2,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                2)), balloon.balloon.posHprInterval(11.5, Point3(230, -140, 175), (-70,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   0)), balloon.balloon.posHprInterval(15.0, Point3(221, -133, 208), (-25,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      0,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      0))))
    return flightPaths


def generateToonFlightPaths(balloon):
    toonFlightPaths = []
    toonFlightPaths.append(Sequence(Wait(0.5), base.localAvatar.posInterval(1.5, Point3(239, -251, 31)), base.localAvatar.posInterval(1.5, Point3(252, -251, 33)), base.localAvatar.posInterval(8.0, Point3(258, -159, 43)), base.localAvatar.posInterval(6.5, Point3(250, -140, 76)), base.localAvatar.posInterval(7.0, Point3(182.88, -135.4, 78.686)), base.localAvatar.posInterval(4.0, Point3(124.97, -82.71, 94.949)), base.localAvatar.posInterval(5.5, Point3(187.85, 34.398, 102.08)), base.localAvatar.posInterval(10.0, Point3(270, 15, 101)), base.localAvatar.posInterval(4.5, Point3(273, -32, 104)), base.localAvatar.posInterval(5, Point3(307, -100, 112)), base.localAvatar.posInterval(5, Point3(320, -168, 112)), base.localAvatar.posInterval(11.5, Point3(230, -140, 175)), base.localAvatar.posInterval(15.0, Point3(221, -133, 208))))
    return toonFlightPaths


def generateSpeechSequence(balloon):
    speechSequence = Sequence(Func(balloon.alec.setChatAbsolute, AlecSpeeches[0], CFSpeech | CFTimeout), Wait(9.5), Func(balloon.alec.setChatAbsolute, AlecSpeeches[1], CFSpeech | CFTimeout), Wait(9.5), Func(balloon.alec.setChatAbsolute, AlecSpeeches[2], CFSpeech | CFTimeout), Wait(9.5), Func(balloon.alec.setChatAbsolute, AlecSpeeches[3], CFSpeech | CFTimeout), Wait(9.5), Func(balloon.alec.setChatAbsolute, AlecSpeeches[4], CFSpeech | CFTimeout), Wait(9.5), Func(balloon.alec.setChatAbsolute, AlecSpeeches[5], CFSpeech | CFTimeout), Wait(9.5), Func(balloon.alec.setChatAbsolute, AlecSpeeches[6], CFSpeech | CFTimeout), Wait(9.5), Func(balloon.alec.setChatAbsolute, AlecSpeeches[7], CFSpeech | CFTimeout), Wait(9.5), Func(balloon.alec.setChatAbsolute, AlecSpeeches[8], CFSpeech | CFTimeout), Wait(9.5), Func(balloon.alec.setChatAbsolute, AlecSpeeches[9], CFSpeech | CFTimeout))
    return speechSequence