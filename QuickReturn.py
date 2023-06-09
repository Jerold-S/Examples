from numpy import deg2rad, rad2deg, array, zeros, linspace, pi
from sympy import symbols, trigsimp, simplify
from sympy import pi as sy_pi
from sympy.physics.mechanics import *
from scipy.integrate import odeint
from pydy.codegen.ode_function_generators import generate_ode_function
import matplotlib.pyplot as plt 
from sympy.physics.vector import init_vprinting


## Reference Frames/Rigid Bodies

q1, q2, q3, q4, q5 ,q6= dynamicsymbols('q1, q2, q3, q4, q5,q6') # Angles
q1_d, q2_d, q3_d, q4_d, q5_d, q6_d = dynamicsymbols('q1, q2, q3, q4, q5, q6', 1) # Differentials of Angles
u1, u2, u3, u4, u5, u6 = dynamicsymbols('u1, u2, u3, u4, u5, u6')

L, r1, r2, d1, d2 , I1, I2, I3, m = symbols('L, r1, r2, d1, d2 , I1, I2, I3, m')

N = ReferenceFrame('N') # Intertial Reference Frame
OP = N.orientnew('OP', 'Axis', [q1, N.z])
MQ = N.orientnew('MQ', 'Axis', [q2, N.z])
QR = N.orientnew('QR', 'Axis', [-(sy_pi/2 - q3), N.z])
ADD = N.orientnew('ADD', 'Axis', [q6, N.z])

# Set Angular velocities of reference frames
OP.set_ang_vel(N, u1 * N.z)
MQ.set_ang_vel(N, u2 * N.z)
QR.set_ang_vel(N, u3 * N.z)
ADD.set_ang_vel(N, u6 * N.z)

#Set Points
O = Point('O')
P1 = O.locatenew('P1', r1 * OP.y) # contact point of OP to MQ
G1 = O.locatenew('G1', r1/2 * OP.y) # centre of mass for OP

M = O.locatenew('M', -d1 * N.y) # Pivot of MQ
P2 = M.locatenew('P2', q4 * MQ.y) # Contact point of MQ to OP
Q = M.locatenew('Q', L * MQ.y) # End of MQ
G2 = M.locatenew('G2', L/2 * MQ.y) # Centre of mass of MQ

G3 = Q.locatenew('G3', r2/2 * QR.y) #Centre of mass of QR
R1 = Q.locatenew('R1', r2 * QR.y) # Contact point of QR to the Slider in N.x
R2 = M.locatenew('R2', (d1 + d2) * N.y + q5 * N.x) # Contact point of the Slider in N.x to QR

F = R1.locatenew('F', r1 * ADD.y)
G4 = R1.locatenew('F', r1/2 * ADD.y)

# Defining Point Velocities
O.set_vel(N, 0)
P1.v2pt_theory(O, N, OP)

M.set_vel(N, 0)
P2.v2pt_theory(M, N, MQ)
Q.v2pt_theory(M, N, MQ)

R1.v2pt_theory(Q, N, QR)
# R2.v2pt_theory(Q, N, QR)

F.v2pt_theory(R1, N, ADD)
G4.v2pt_theory(R1, N, ADD)

#constraints
zero1 = P1.pos_from(O) + O.pos_from(P2)
zero2 = R2.pos_from(M) + M.pos_from(R1)

q_cons = [zero1 & N.x, zero1 & N.y,
          zero2 & N.x, zero2 & N.y] # configuration constraints

dzero1 = time_derivative(zero1, N)
dzero2 = time_derivative(zero2, N)

u_cons = [dzero1 & N.x, dzero1 & N.y,
          dzero2 & N.x, dzero2 & N.y]# velocity constraints

q = [q1, q6] # independant coordinates
u = [u1, u6] # independant velocities
q_dep = [q2, q3, q4, q5] # dependant coordinates
u_dep = [u2, u3, u4, u5] # dependant velocities

coordinates = [q1, q2, q3, q4, q5, q6] # List containing independent generalised coordinates
speeds = [u1, u2, u3, u4, u5, u6] # List containing independent generalised speeds

# Create a list containing the kinematic differential equiations
kde = [u1 - q1_d, u2 - q2_d, u3 - q3_d, u4 - q4_d, u5 - q5_d, u6 - q6_d]

# Generate the equiations of motion, storing the data using the KanesMethod Object
kane = KanesMethod(N, q_ind=q, u_ind=u, kd_eqs= kde,
                   q_dependent=q_dep, u_dependent=u_dep,
                   configuration_constraints=q_cons, velocity_constraints=u_cons)

#defining rigid bodies and particles
crank = RigidBody('Crank', G1, OP, m, (inertia(OP, 0, 0, I1), G1))
s_arm = RigidBody('Slotted Arm', G2, MQ, m, (inertia(MQ, 0, 0, I2), G2))
con = RigidBody('Connecting Rod', G3, QR, m, (inertia(QR, 0, 0, I3), G3))
slider1 = Particle('Slider 1', P1, m)
slider2 = Particle('Slider 2', R1, m)
AddBody = RigidBody('AdditionalBody', G4, ADD, m, (inertia(QR, 0, 0, I3), G4))

# Defining Lists of Bodies and Loads
bodies = [crank, s_arm, con, slider1, slider2, AddBody]

g = symbols('g')

loads = [
    (G1, -g * m * N.y),
    (G2, -g * m * N.y),
    (G3, -g * m * N.y),
    (P2, 0 * N.y),
    (R2, 0 * N.y)
         ]

#Defining Lists containing Bodies and Loads
fr, frstar = kane.kanes_equations(bodies, loads)

#Obtain the Mass Matrix and the Forcing Vector

mm = kane.mass_matrix_full
fm = kane.forcing_full

#Create a list for all the constants

constants = [r1, r2, L, d1, d2, m, I1, I2, I3, g]

#Generate the ODE integrable RHS function
rhs = generate_ode_function(fm, coordinates, speeds, constants, mass_matrix = mm)

# Specify the initial condition
x0 = [deg2rad(48.169), deg2rad(18.195), deg2rad(20.487), 11.931, 0, 0,
      10, 3.63, 3.63, -24.987, -58.08, 0] # Define initial conditions

#Supply numerical values for the constants
num_constants = array([5, 5, 15, 8, 8, 12, 6.25, 56.25, 6.25, 9.81])

#Time over which eqations to be integrated over
t = linspace(0, 2, 2000)

rhs(x0, 0.0, num_constants)

y = odeint(rhs, x0, t, args = (num_constants, ))


### Visulisation using pydy.vis

from pydy.viz.shapes import Cylinder, Cube
import pydy.viz
from pydy.viz.visualization_frame import VisualizationFrame
from pydy.viz.scene import Scene

# Dictionary mapping the constant symbols to their numerical values
constants_dict = dict(zip(constants, num_constants))

crank_shape = Cylinder(length = constants_dict[r1], radius = 0.1, color = 'grey')
s_arm_shape = Cylinder(length = constants_dict[L], radius = 0.1, color = 'blue')
connecRod_Shape = Cylinder(length = constants_dict[r2], radius = 0.1, color = 'green')
add_shape = Cylinder(length= constants_dict[r1], radius = 0.1, color = 'yellow')

Slider1_shape = Cube(length = 0.2, color = 'red') 
Slider2_shape = Cube(length = 0.2, color = 'red') 

cr_vf = VisualizationFrame('Crank', OP, G1, crank_shape)
sl_vf = VisualizationFrame('Slotted Arm', MQ, G2, s_arm_shape)
cn_vf = VisualizationFrame('Connecting Rod', QR, G3, connecRod_Shape)
add_vf = VisualizationFrame('Additional', ADD, G4, connecRod_Shape)

s1_vf = VisualizationFrame('Slider 1', MQ, slider1, Slider1_shape)
s2_vf = VisualizationFrame('Slider 2', QR, slider2, Slider2_shape)


scene = Scene(N, O)
scene.visualization_frames = [cr_vf, sl_vf, cn_vf, s1_vf, s2_vf, add_vf]
scene.states_symbols = coordinates + speeds
scene.constants = constants_dict
scene.states_trajectories = y
scene.times = t
scene.display()