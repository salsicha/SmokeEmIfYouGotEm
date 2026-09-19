"""Physical-energy pullback to original moving-front geometry primitives.

Differentiate the SAME two-pole kinetic energy in both momentum coordinates.
Shared face
columns, local depth moments and bed gradients remain independent arguments;
their physical evolution must still be supplied by the coupled conservation
law. This is not a force closure, open-boundary solver or gameplay acceptance.
"""
from fractions import Fraction as F


class FrontPressureVariation:
    """Exact reverse derivative, without differentiating a numerical solve.

    For H_j=M+lambda_j*C, a_j=H_j^-1*M*v and p=B*v, at fixed p:
    E_M=-c*v*v/2-sum(w_j*(v*a_j-a_j*a_j/2)),
    E_C=sum(w_j*lambda_j*a_j*a_j^T/2).
    Reverse C=sum(J_i^T*G_i*J_i) through the actual common columns
    and EACH owner's volume denominator, then through the depth-moment Gram form.
    Gravitational potential and the transport bracket are NOT included.
    """
    def __init__(self, geometry, metric, physical_momentum, *, solved_state=None):
        if hasattr(metric, 'linear'):
            raise ValueError('Affine prescribed trace requires AffineFrontPressureVariation, not reflecting derivatives')
        g,m=geometry,metric;zero=m.zero;n=len(g.active)
        if (tuple(m.mass)!=tuple(v for v in g.volumes for _ in range(2)) or
                m.kinetic!=tuple(map(tuple,g.kinetic))):
            raise ValueError('Matching original source mass and pressure geometry required')
        self.geometry=g;self.zero=zero;self.number=m.number
        p=m.vector(physical_momentum)
        # An original exact solve may be expensive. Reuse only its unknowns,
        # never its reported success flags or precomputed gradients. The original
        # pole equations and physical-momentum reconstruction below still prove
        # that these are the unique solution for THIS geometry and input.
        if solved_state is None:
            v=m.solve_physical.solve(p);auxiliaries=None
        else:
            v=m.vector(solved_state['canonical_velocity'])
            states=solved_state['poles']
            if len(states)!=len(m.poles) or any(
                    m.number(state['length'])!=pole['length'] or m.number(state['weight'])!=pole['weight']
                    for state,pole in zip(states,m.poles)):
                raise ValueError('Both original pressure poles in original order required')
            auxiliaries=tuple(m.vector(state['auxiliary_velocity']) for state in states)
        self.momentum_gradient=m.pairs(v)
        mass=[-m.constant*x*x/2 for x in v]
        matrix=[[zero]*(2*n) for _ in range(2*n)]
        grams=[[[zero]*3 for _ in range(3)] for _ in range(n)]
        divergence=[[zero]*(2*n) for _ in range(n)]
        reconstructed=[m.constant*mi*vi for mi,vi in zip(m.mass,v)]
        for index,pole in enumerate(m.poles):
            a=m.action(pole['auxiliary_map'],v) if auxiliaries is None else auxiliaries[index]
            if m.action(pole['matrix'],a)!=tuple(mi*vi for mi,vi in zip(m.mass,v)):
                raise ValueError('Original pressure pole residual is nonzero')
            w,lam=pole['weight'],pole['length']
            for i in range(2*n):
                mass[i]-=w*(v[i]*a[i]-a[i]*a[i]/2)
                reconstructed[i]+=w*m.mass[i]*a[i]
                for j in range(2*n):matrix[i][j]+=w*lam*a[i]*a[j]/2
            for row,owner in enumerate(g.active):
                jet=(sum((x*y for x,y in zip(g.divergence[row],a)),zero),a[2*row],a[2*row+1])
                gram=g.forms[owner]['gram']
                force0=sum((x*y for x,y in zip(gram[0],jet)),zero)
                for i in range(3):
                    for j in range(3):grams[row][i][j]+=w*lam*jet[i]*jet[j]/2
                for i in range(2*n):divergence[row][i]+=w*lam*force0*a[i]
        if tuple(reconstructed)!=p:raise ValueError('Original two-pole momentum reconstruction failed')
        self.mass_gradient=tuple(mass)
        self.kinetic_gradient=tuple(map(tuple,matrix))
        self.gram_gradients=tuple(tuple(map(tuple,gram)) for gram in grams)
        self.divergence_gradients=tuple(map(tuple,divergence))
        volume=[mass[2*i]+mass[2*i+1]-sum((a*b for a,b in zip(divergence[i],g.divergence[i])),zero)/g.volumes[i]
                for i in range(n)]
        self.volume_gradient=tuple(volume)
        positions={owner:i for i,owner in enumerate(g.active)}
        faces=[]
        for face in g.faces:
            owners=face['owners']
            if any(owner not in positions for owner in owners):
                if any(x!=0 for x in (*face['column_normal'],*face['column_normal_rate'])):
                    raise ValueError('Dry owner cannot carry a pressure column or column rate')
                # No differentiable active velocity exists on a dry owner.
                # Its derivative is unsupported, not an invented zero force.
                faces.append(None);continue
            li=positions[owners[0]];divisor=len(owners)
            if divisor not in (1,2):raise ValueError('One or two original pressure-face owners required')
            gradient=[]
            for axis in range(2):
                value=zero
                for owner in owners:
                    row=positions[owner]
                    term=-divergence[row][2*li+axis]
                    if divisor==2:term+=divergence[row][2*positions[owners[1]]+axis]
                    value+=term/(divisor*g.volumes[row])
                gradient.append(value)
            faces.append(tuple(gradient))
        self.face_column_gradients=tuple(faces)
        moments=[];slopes=[]
        for row,owner in enumerate(g.active):
            gram=grams[row];x,y=g.fragments[owner].gradient
            _,m1,m2,_=g.forms[owner]['depth_moments']
            moments.append((volume[row]+3*(x*x*gram[1][1]+2*x*y*gram[1][2]+y*y*gram[2][2]),
                            -3*(x*gram[0][1]+y*gram[0][2]),gram[0][0]))
            slopes.append((-3*m2*gram[0][1]+6*m1*(x*gram[1][1]+y*gram[1][2]),
                           -3*m2*gram[0][2]+6*m1*(x*gram[1][2]+y*gram[2][2])))
        self.depth_moment_gradients=tuple(moments)
        self.bed_gradient_gradients=tuple(slopes)
        # At fixed canonical momentum m=M*v the energy is +v^T*B*v/2.
        # The geometry derivative changes sign AND differentiates v=m/M.
        # Its momentum conjugate is the layer velocity p/M, not v.
        self.canonical_momentum_gradient=m.pairs(tuple(x/mi for x,mi in zip(p,m.mass)))
        self.canonical_depth_moment_gradients=tuple(
            (-moments[i][0]-sum((p[2*i+a]*v[2*i+a] for a in range(2)),zero)/g.volumes[i],
             -moments[i][1],-moments[i][2]) for i in range(n))
        self.canonical_face_column_gradients=tuple(None if row is None else tuple(-x for x in row) for row in faces)
        self.canonical_bed_gradient_gradients=tuple(tuple(-x for x in row) for row in slopes)

    def work(self, momentum_direction, moment_direction, face_column_direction, bed_gradient_direction,
             *, momentum_coordinate='physical'):
        """Contract an explicit physical primitive direction at fixed topology.

        Dry-face creation is rejected rather than assigned a fabricated force.
        Wet-area/topology motion and open exterior work are not inferred here.
        """
        if momentum_coordinate not in ('physical','canonical'):
            raise ValueError('Explicit physical or canonical momentum coordinate required')
        prefix='canonical_' if momentum_coordinate=='canonical' else ''
        groups=((getattr(self,prefix+'momentum_gradient'),momentum_direction,2),
                (getattr(self,prefix+'depth_moment_gradients'),moment_direction,3),
                (getattr(self,prefix+'bed_gradient_gradients'),bed_gradient_direction,2))
        terms=[]
        for gradients,direction,width in groups:
            direction=tuple(tuple(self.number(x) for x in row) for row in direction)
            if len(gradients)!=len(direction) or any(len(row)!=width for row in direction):
                raise ValueError('One matching primitive direction per active original source required')
            terms.append(sum((a*b for row,delta in zip(gradients,direction) for a,b in zip(row,delta)),self.zero))
        faces=tuple(tuple(self.number(x) for x in row) for row in face_column_direction)
        face_gradients=getattr(self,prefix+'face_column_gradients')
        if len(faces)!=len(face_gradients) or any(len(row)!=2 for row in faces):
            raise ValueError('One directed column variation per original face required')
        column=self.zero
        for gradient,direction in zip(face_gradients,faces):
            if gradient is None:
                if any(x!=0 for x in direction):raise ValueError('Dry pressure topology creation needs a coupled front law')
            else:column+=sum((a*b for a,b in zip(gradient,direction)),self.zero)
        return dict(momentum_work=terms[0],depth_moment_work=terms[1],bed_gradient_work=terms[2],
                    face_column_work=column,energy_direction=sum(terms,self.zero)+column,
                    momentum_coordinate=momentum_coordinate,
                    nonlinear_force_or_topology_change_or_gameplay_accepted=False)

    def time_work(self, momentum_rate, *, momentum_coordinate='physical'):
        g=self.geometry
        return self.work(momentum_rate,[g.forms[i]['depth_moment_rates'] for i in g.active],
                         [f['column_normal_rate'] for f in g.faces],[(F(0),F(0)) for _ in g.active],
                         momentum_coordinate=momentum_coordinate)
