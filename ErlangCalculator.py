'''

Functions that provide the basic information for sizing of a contact center
Author: Cleverson Ezequiel Silva Sobrinho


'''
import math

# =====================================
# Declarating constants

MAXACCURACY = 0.000001
MAXLOOPS = 1000
TIMEINTERVAL = 1800  # this represents half of an hour in seconds, in case of a measure for One hour Interval,
# this must be changed to 3600

# ======================================
# Function that limits an value between a defined interval


def MinMax(x, min=0, max=1):
    if x > max:
        return max
    elif x < min:
        return min
    else:
        return x


# ======================================
# Function that estimate the likelihood of blocking all channel for a certain number of agents and traffic
def ErlangB(Servers, Intensity):
    try:
        if Servers == 0 or Intensity == 0:
            return 0
        maxiterate = int(Servers) + 1
        val = Intensity
        last = 1
        b = 0
        for count in range(1, maxiterate):
            b = (val * last) / (count + (val * last))
            last = b
        return MinMax(b)
    except ValueError as error:
        return 0


# ======================================
# Function that estimate the likelihood of blocking all channel for a certain number of agents and traffic
# and a percent of callers will return immediately
def ErlangBExt(Servers, Intensity, Retry):
    try:
        if Servers == 0 or Intensity == 0:
            return 0
        maxiterate = int(Servers) + 1
        retries = MinMax(Retry)
        val = Intensity
        last = 1
        b = 0
        for count in range(1, maxiterate):
            b = (val * last) / (count + (val * last))
            attempts = 1 / (1 - (b * retries))
            b = (val * last * attempts) / (count + (val * last * attempts))
            last = b
        return MinMax(b)
    except ValueError as error:
        return 0


# =============================================
# function for calculation of blocking channels through Engset
def EngsetB(Servers, Events, Intensity):
    try:
        if Servers == 0 or Intensity == 0:
            return 0
        maxiterate = int(Servers) + 1
        val = Intensity
        Ev = Events
        last = 1
        b = 0
        for count in range(1, maxiterate):
            b = (last * (count / ((Ev - count) * val))) + 1
            last = b
        if b == 0:
            return 0
        else:
            return MinMax((1 / b))
    except ValueError as error:
        return 0


# ======================================
def ErlangC(Servers, Intensity):
    try:
        if Servers < 0 or Intensity < 0:
            return 0
        b = ErlangB(Servers, Intensity)
        c = b / (((Intensity / Servers) * b) + (1 - (Intensity / Servers)))
        return MinMax(c)
    except ValueError as error:
        return 0


# ===================================

def NBTrunks(Intensity, Blocking):
    try:
        if Intensity <= 0 or Blocking <= 0:
            return 0
        maxiterate = 2 ** 16  # limits the number of iterations for better process
        for count in range(math.ceil(Intensity), maxiterate + 1):
            sngcount = count
            b = ErlangB(sngcount, Intensity)
            if b <= Blocking:
                return sngcount
                break
        if sngcount == maxiterate:
            return 0
    except ValueError as error:
        return 0


# ===================================

def NumberTrunks(Servers, Intensity):
    try:
        if Servers < 0 or Intensity < 0:
            return 0
        maxiterate = 2 ** 16
        for count in range(math.ceil(Servers), maxiterate + 1):
            server = count
            b = ErlangB(server, Intensity)
            if b < 0.001:
                return count
                break
    except ValueError as error:
        return 0


# ===================================

def Servers(Blocking, Intensity):
    try:
        if Blocking < 0 or Intensity < 0:
            return 0
        val = Intensity
        last = 1
        b = 1
        count = 0
        while b > Blocking and b > 0.001:
            count += 1
            b = (val * last) / (count + (val * last))
            last = b
        return count
    except ValueError as error:
        return 0


# ====================================================

def LoopingTraffic(Trunks, Blocking, Increment, MaxIntensity, MinIntensity):
    try:
        MinI = MinIntensity
        b = ErlangB(Trunks, MinI)
        if b == Blocking:
            return MinI
        inc = Increment
        Intensity = MinI
        LoopNo = 0
        while inc >= MAXACCURACY and LoopNo < MAXLOOPS:
            b = ErlangB(Trunks, Intensity)
            if b > Blocking:
                MaxI = Intensity
                inc /= 10
                Intensity = MinI
            MinI = Intensity
            Intensity += inc
            LoopNo += 1
        return MinI
    except ValueError as error:
        return 0


# ====================================================

def Traffic(Servers, Blocking):
    try:
        trunks = int(Servers)

        if Servers < 1 or Blocking < 0:
            return 0
        maxiterate = trunks
        b = ErlangB(Servers, maxiterate)

        while b < Blocking:
            maxiterate *= 2
            b = ErlangB(Servers, maxiterate)
        inc = 1
        while inc <= maxiterate / 100:
            inc *= 10
        return LoopingTraffic(trunks, Blocking, inc, maxiterate, 0)
    except ValueError as error:
        return 0


# ====================================================

def Abandon(Agents, AbandonTime, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        c = ErlangC(server, trafficrate)
        aband = c * math.exp((trafficrate - server) * (AbandonTime / AHT))
        return MinMax(aband)
    except ValueError as error:
        return 0


# ====================================================

def Agents(SLA, ServiceTime, CallsPerHour, AHT):
    try:
        sla = MinMax(SLA)

        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        erlangs = (birthrate * AHT) / TIMEINTERVAL
        agents = 1 if erlangs < 1 else math.ceil(erlangs)
        utilisation = trafficrate / agents
        while utilisation >= 1:
            agents += 1
            utilisation = trafficrate / agents
        maxiterate = agents * 100 + 1
        for count in range(1, maxiterate):
            if utilisation < 1:
                server = agents
                c = ErlangC(server, trafficrate)
                slqueued = 1 - c * (math.exp((trafficrate - server) * ServiceTime / AHT))
                if slqueued < 0:
                    slqueued = 0
                if slqueued > SLA:
                    return agents
                    break
                elif slqueued > (1 - MAXACCURACY):
                    return agents
                    break
            agents += 1
    except ValueError as error:
        return 0


# ====================================================

def AgentsASA(ASA, CallsPerHour, AHT):
    try:
        asa = 1 if ASA < 0 else ASA
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        erlangs = birthrate * AHT / TIMEINTERVAL
        agents = 1 if erlangs < 1 else int(erlangs)
        utilisation = trafficrate / agents
        while utilisation >= 1:
            agents += 1
            utilisation = trafficrate / agents
        maxiterate = agents * 100 + 1
        for count in range(1, maxiterate):
            server = agents
            utilisation = trafficrate / agents
            c = ErlangC(server, trafficrate)
            answertime = c / (server * deathrate * (1 - utilisation))
            if answertime * TIMEINTERVAL <= asa:
                return agents
                break
            agents += 1
    except ValueError as error:
        return 0


# ====================================================

def ASA(Agents, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        utilisation = trafficrate / server if trafficrate < server else 0.99
        c = ErlangC(server, trafficrate)
        answertime = c / (server * deathrate * (1 - utilisation))
        return int(answertime * TIMEINTERVAL + 0.5)
    except ValueError as error:
        return 0


# ====================================================

def NBAgents(CallsPerHour, avgSA, AHT):
    try:
        if CallsPerHour <= 0 or avgSA <= 0 or AHT <= 0:
            return 0
        maxiterate = 2 ** 16
        for count in range(1, maxiterate + 1):
            sngcount = count
            b = ASA(sngcount, CallsPerHour, AHT)
            if b <= avgSA:
                return count
                break
        if sngcount == maxiterate:
            return 0
    except ValueError as error:
        return 0


# ====================================================

def CallCapacity(NoAgents, SLA, ServiceTime, AHT):
    try:
        agents = int(NoAgents)
        calls = math.ceil(TIMEINTERVAL / AHT) * agents
        agent = Agents(SLA, ServiceTime, calls, AHT)
        while agent > agents and calls > 0:
            calls -= 1
            agent = Agents(SLA, ServiceTime, calls, AHT)
        return calls
    except ValueError as error:
        return 0


# ====================================================

def FractionalAgents(SLA, ServiceTime, CallsPerHour, AHT):
    try:
        sla = MinMax(SLA)
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        erlangs = birthrate * AHT / TIMEINTERVAL
        agents = 1 if erlangs < 1 else int(erlangs + 0.5)
        utilisation = trafficrate / agents
        while utilisation >= 1:
            agents += 1
            utilisation = trafficrate / agents
        slqueued = 0
        maxiterate = agents * 100
        lastslq = 0
        for count in range(1, maxiterate + 1):
            lastslq = slqueued
            utilisation = trafficrate / agents
            if utilisation < 1:
                server = agents
                c = ErlangC(server, trafficrate)
                slqueued = MinMax(1 - c * math.exp((trafficrate - server) * ServiceTime / AHT))
                if slqueued > sla:
                    break
                elif slqueued > (1 - MAXACCURACY):
                    break
            agents += 1
        agentssng = agents
        if slqueued > sla:
            oneagent = slqueued - lastslq
            fract = sla - lastslq
            agentssng = (fract / oneagent) + (agents - 1)
        return agentssng
    except ValueError as error:
        return 0


# ====================================================

def FractionalCallCapacity(NoAgents, SLA, ServiceTime, AHT):
    try:
        xnoagents = NoAgents
        calls = math.ceil(TIMEINTERVAL / AHT * xnoagents)
        xagent = FractionalAgents(SLA, ServiceTime, calls, AHT)
        while xagent > xnoagents and calls > 0:
            calls -= 1
            xagent = FractionalAgents(SLA, ServiceTime, calls, AHT)
        return calls
    except ValueError as error:
        return 0


# ====================================================

def Queued(Agents, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        q = ErlangC(server, trafficrate)
        return MinMax(q)
    except ValueError as error:
        return 0


# ====================================================

def QueueSize(Agents, CallsPerhour, AHT):
    try:
        birthrate = CallsPerhour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        utilisation = trafficrate / server if trafficrate < server else 0.99
        c = ErlangC(server, trafficrate)
        qsize = utilisation * c / (1 - utilisation)
        return int(qsize + 0.5)
    except ValueError as error:
        return 0


# ====================================================

def QueueTime(Agents, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        utilisation = trafficrate / server if trafficrate < server else 0.99
        qtime = 1 / (server * deathrate * (1 - utilisation))
        return int(qtime * TIMEINTERVAL + 0.5)
    except ValueError as error:
        return 0


# ====================================================

def ServiceTime(NoAgents, SLA, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = NoAgents
        c = ErlangC(server, trafficrate)
        utilisation = trafficrate / server if trafficrate < server else 0.99
        qtime = (1 / (server * deathrate * (1 - utilisation))) * TIMEINTERVAL
        stime = qtime * (1 - ((1 - SLA) / c))
        ag = Agents(SLA, int(stime), CallsPerHour, AHT)
        adjust = 0 if ag == NoAgents else 1
        return int(stime + adjust)
    except ValueError as error:
        return 0


# ====================================================

def SLA(Agents, ServiceTime, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        c = ErlangC(server, trafficrate)
        slqueued = 1 - c * math.exp((trafficrate - server) * ServiceTime / AHT)
        return MinMax(slqueued)
    except ValueError as error:
        return 0


# ====================================================

def Trunks(Agents, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        utilisation = trafficrate / server if trafficrate < server else 0.99
        c = ErlangC(server, trafficrate)
        answertime = c / (server * deathrate * (1 - utilisation))
        secanstime = int(answertime * TIMEINTERVAL + 0.5)
        r = birthrate / (TIMEINTERVAL / (AHT + secanstime))
        ntrunks = NumberTrunks(server, r)
        trunks = 1 if ntrunks < 1 and trafficrate > 0 else ntrunks
        return trunks
    except ValueError as error:
        return 0


# ====================================================

def Utilisation(Agents, CallsPerHour, AHT):
    try:

        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        utilisation = trafficrate / Agents
        return MinMax(utilisation)
    except ValueError as error:
        return 0


# ====================================================

if __name__ == "__main__":
    print('================================================================================================')
    print()
    print()
    print(f'Funções desenvolvidas para calcular os principais parâmetros de dimensionamento de Call Centers')
    print()
    print()
    print('================================================================================================')
