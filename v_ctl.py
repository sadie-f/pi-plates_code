#!/usr/bin/python
"""
TODO:
  *** review (fix) state transition logic in code
    complete all state transition variables

    ?? add per-motor locks in /var/tmp 
      (cmd input  interface maybe easiest place for this, it's a choke-point)
    write wrappers .. interface?
      ?? start taking commands from either a named pipe, socket, regular file?
    timescaledb writes (via popen)
    
"""
import signal
import piplates.MOTORplate as MOTOR
import time
import sys

# global motion variables

card = int(sys.argv[1])
motor = sys.argv[2]


position = 0
direction = 'ccw'
velocity = 400
accel = 1

# state machine 
mode = "disable"

disabled = 1
enabled = 0
stopped = 1
moving = 0
jogging = 0


def signal_handler(sig, frame):     # try 'None' instead of 'frame'sen
    global card
    global motor
    global accel
    MOTOR.stepperSTOP (card, motor)
    time.sleep (0.1)
    stopped = 1
    
    MOTOR.clrLED(0)
    time.sleep (accel)
    MOTOR.stepperOFF (card, motor)
    enabled = 0
    disabled = 1
    print('You pressed Ctrl+C!')
    sys.exit(1)
    
signal.signal(signal.SIGINT, signal_handler)


def cmd_in():
    print "entering function cmd"
    cmdstr = sys.stdin.readline()
    print >> sys.stderr, cmdstr
    cmd = cmdstr.split()
    return cmd

def ax_enable():
    print "entering function ax"
    #enable motors note: can't move 0 distance (= jog) move -1/+1 instead
    MOTOR.stepperCONFIG(card, 'a', 'cw', 3, velocity, accel)
    MOTOR.stepperMOVE(card, 'a', 1)
    MOTOR.stepperCONFIG(card, 'a', 'ccw', 3, velocity, accel)
    MOTOR.stepperMOVE(card, 'a', 1)
    MOTOR.stepperCONFIG(card, 'b', 'cw', 3, velocity, accel)
    MOTOR.stepperMOVE(card, 'b', 1)
    MOTOR.stepperCONFIG(card, 'b', 'ccw', 3, velocity, accel)
    MOTOR.stepperMOVE(card, 'b', 1)
    MOTOR.setLED(0)

    enabled = 1
    disabled = 0

    while (1):
        e_cmd = cmd_in()
        if (e_cmd[0] == "s"):
            stop ()
        elif (e_cmd[0] == "g"):
            move (int (e_cmd[1]))
        elif (e_cmd[0] == "r"):
            move_rel (int (e_cmd[1]))
        elif (e_cmd[0] == "j"):
            jog (e_cmd[1])
        elif (e_cmd[0] == "q"):
            sys.exit(0)
        else:
            print >> sys.stderr, "Invalid command: error in enable state\n"
        
def stop():    
    global position
    global moving
    global jogging
    print "entered stop "
    moving = 0
    jogging = 0
    stopped = 1
    MOTOR.clrLED(0)
    MOTOR.stepperSTOP (card, motor)
    position = 0
    
def move (loc):

    global position
    global moving
    global accel
    global velocity
    print "entered move = ", loc
    if (loc <0 ):
        error=1
        print >> sys.stderr, "Invalid move (negative postion) aborting\n"
        return(error)
    else:
        m_dist = loc - position
        if (m_dist == 0):
            error=2
            print >> sys.stderr, "Invalid move (0 steps), aborting\n"
            return (error)
        elif (m_dist < 0):
            direction = 'cw'
        else:
            direction = 'ccw'
    position += m_dist
    print "move motor", m_dist
    m_dist = abs (m_dist)
    
    MOTOR.stepperCONFIG(card, motor, direction, 3, velocity, accel)
    stopped = 0
    moving = 1
    MOTOR.setLED(0)
    MOTOR.stepperMOVE(card, motor, m_dist)
    delay = m_dist / velocity
    delay += accel
    time.sleep(delay)
    moving = 0
    stopped = 1
    MOTOR.clrLED(0)
        
def move_rel (m_dist):
    global position
    global moving
    global accel
    global velocity

    if (position + m_dist < 0):
        error = 3
        print >> sys.stderr, "Invalid relative move (negative postion) aborting\n"
        return (error)
    
    if (dist < 0):
        direction = 'cw'
    else:
        direction = 'ccw'
    position += m_dist
    
    MOTOR.stepperCONFIG(card, motor, direction, 3, velocity, accel)
    stopped = 0
    moving = 1
    MOTOR.setLED(0)
    MOTOR.move(card, motor, m_dist)
    delay = m_dist / velocity
    delay += accel
    time.sleep(delay)
    moving = 0
    stopped = 1
    MOTOR.clrLED(0)

def jog (jdir):
    global position
    global moving
    global jogging
    global accel
    global velocity

    if (jdir == '+'):
        jdir = 'ccw'
    elif (jdir == '-'):
        jdir = 'cw'
    else:
        print >> sys.stderr, "Invalid direction error in jog state\n"
    position = 0
    jogging = 1
    moving = 1
    MOTOR.stepperCONFIG(card, motor, jdir, 3, velocity, accel)
    MOTOR.setLED(0)
    MOTOR.stepperJOG(card, motor)
    
print "begin"
while (1):
    root_cmd = cmd_in()
    if (root_cmd[0] == "e"):
        print "call function ax"
        rslt = ax_enable()
        print "result = ", rslt
    else:
        print >> sys.stderr, "Invalid command: error from init / disable state"

