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


def min_max(x, min=0, max=1):
    if x > max:
        return max
    elif x < min:
        return min
    else:
        return x


# ======================================
# Function that estimate the likelihood of blocking all channel for a certain number of agents and traffic
def erlang_b(Servers, Intensity):
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
        return min_max(b)
    except ValueError as error:
        return 0


# ======================================
# Function that estimate the likelihood of blocking all channel for a certain number of agents and traffic
# and a percent of callers will return immediately
def erlang_b_ext(Servers, Intensity, Retry):
    try:
        if Servers == 0 or Intensity == 0:
            return 0
        maxiterate = int(Servers) + 1
        retries = min_max(Retry)
        val = Intensity
        last = 1
        b = 0
        for count in range(1, maxiterate):
            b = (val * last) / (count + (val * last))
            attempts = 1 / (1 - (b * retries))
            b = (val * last * attempts) / (count + (val * last * attempts))
            last = b
        return min_max(b)
    except ValueError as error:
        return 0


# =============================================
# function for calculation of blocking channels through Engset
def engset_b(Servers, Events, Intensity):
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
            return min_max((1 / b))
    except ValueError as error:
        return 0


# ======================================
def erlang_c(Servers, Intensity):
    try:
        if Servers < 0 or Intensity < 0:
            return 0
        b = erlang_b(Servers, Intensity)
        c = b / (((Intensity / Servers) * b) + (1 - (Intensity / Servers)))
        return min_max(c)
    except ValueError as error:
        return 0


# ===================================

def nb_trunks(Intensity, Blocking):
    try:
        if Intensity <= 0 or Blocking <= 0:
            return 0
        maxiterate = 2 ** 16  # limits the number of iterations for better process
        for count in range(math.ceil(Intensity), maxiterate + 1):
            sngcount = count
            b = erlang_b(sngcount, Intensity)
            if b <= Blocking:
                return sngcount
                break
        if sngcount == maxiterate:
            return 0
    except ValueError as error:
        return 0


# ===================================

def number_trunks(Servers, Intensity):
    try:
        if Servers < 0 or Intensity < 0:
            return 0
        maxiterate = 2 ** 16
        for count in range(math.ceil(Servers), maxiterate + 1):
            server = count
            b = erlang_b(server, Intensity)
            if b < 0.001:
                return count
                break
    except ValueError as error:
        return 0


# ===================================

def servers(Blocking, Intensity):
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

def looping_traffic(Trunks, Blocking, Increment, MaxIntensity, MinIntensity):
    try:
        MinI = MinIntensity
        b = erlang_b(Trunks, MinI)
        if b == Blocking:
            return MinI
        inc = Increment
        Intensity = MinI
        LoopNo = 0
        while inc >= MAXACCURACY and LoopNo < MAXLOOPS:
            b = erlang_b(Trunks, Intensity)
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

def traffic(Servers, Blocking):
    try:
        trunks = int(Servers)

        if Servers < 1 or Blocking < 0:
            return 0
        maxiterate = trunks
        b = erlang_b(Servers, maxiterate)

        while b < Blocking:
            maxiterate *= 2
            b = erlang_b(Servers, maxiterate)
        inc = 1
        while inc <= maxiterate / 100:
            inc *= 10
        return looping_traffic(trunks, Blocking, inc, maxiterate, 0)
    except ValueError as error:
        return 0


# ====================================================

def abandon(Agents, AbandonTime, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        c = erlang_c(server, trafficrate)
        aband = c * math.exp((trafficrate - server) * (AbandonTime / AHT))
        return min_max(aband)
    except ValueError as error:
        return 0


# ====================================================

def agents(SLA, ServiceTime, CallsPerHour, AHT):
    try:
        sla = min_max(SLA)

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
                c = erlang_c(server, trafficrate)
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

def agents_asa(ASA, CallsPerHour, AHT):
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
            c = erlang_c(server, trafficrate)
            answertime = c / (server * deathrate * (1 - utilisation))
            if answertime * TIMEINTERVAL <= asa:
                return agents
                break
            agents += 1
    except ValueError as error:
        return 0


# ====================================================

def asa(Agents, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        utilisation = trafficrate / server if trafficrate < server else 0.99
        c = erlang_c(server, trafficrate)
        answertime = c / (server * deathrate * (1 - utilisation))
        return int(answertime * TIMEINTERVAL + 0.5)
    except ValueError as error:
        return 0


# ====================================================

def nb_agents(CallsPerHour, avgSA, AHT):
    try:
        if CallsPerHour <= 0 or avgSA <= 0 or AHT <= 0:
            return 0
        maxiterate = 2 ** 16
        for count in range(1, maxiterate + 1):
            sngcount = count
            b = asa(sngcount, CallsPerHour, AHT)
            if b <= avgSA:
                return count
                break
        if sngcount == maxiterate:
            return 0
    except ValueError as error:
        return 0


# ====================================================

def call_capacity(NoAgents, SLA, ServiceTime, AHT):
    try:
        agents = int(NoAgents)
        calls = math.ceil(TIMEINTERVAL / AHT) * agents
        agent = agents(SLA, ServiceTime, calls, AHT)
        while agent > agents and calls > 0:
            calls -= 1
            agent = agents(SLA, ServiceTime, calls, AHT)
        return calls
    except ValueError as error:
        return 0


# ====================================================

def fractional_agents(SLA, ServiceTime, CallsPerHour, AHT):
    try:
        sla = min_max(SLA)
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
                c = erlang_c(server, trafficrate)
                slqueued = min_max(1 - c * math.exp((trafficrate - server) * ServiceTime / AHT))
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

def fractional_call_capacity(NoAgents, SLA, ServiceTime, AHT):
    try:
        xnoagents = NoAgents
        calls = math.ceil(TIMEINTERVAL / AHT * xnoagents)
        xagent = fractional_agents(SLA, ServiceTime, calls, AHT)
        while xagent > xnoagents and calls > 0:
            calls -= 1
            xagent = fractional_agents(SLA, ServiceTime, calls, AHT)
        return calls
    except ValueError as error:
        return 0


# ====================================================

def queued(Agents, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        q = erlang_c(server, trafficrate)
        return min_max(q)
    except ValueError as error:
        return 0


# ====================================================

def queue_size(Agents, CallsPerhour, AHT):
    try:
        birthrate = CallsPerhour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        utilisation = trafficrate / server if trafficrate < server else 0.99
        c = erlang_c(server, trafficrate)
        qsize = utilisation * c / (1 - utilisation)
        return int(qsize + 0.5)
    except ValueError as error:
        return 0


# ====================================================

def queue_time(Agents, CallsPerHour, AHT):
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

def service_time(NoAgents, SLA, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = NoAgents
        c = erlang_c(server, trafficrate)
        utilisation = trafficrate / server if trafficrate < server else 0.99
        qtime = (1 / (server * deathrate * (1 - utilisation))) * TIMEINTERVAL
        stime = qtime * (1 - ((1 - SLA) / c))
        ag = agents(SLA, int(stime), CallsPerHour, AHT)
        adjust = 0 if ag == NoAgents else 1
        return int(stime + adjust)
    except ValueError as error:
        return 0


# ====================================================

def sla(Agents, ServiceTime, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        c = erlang_c(server, trafficrate)
        slqueued = 1 - c * math.exp((trafficrate - server) * ServiceTime / AHT)
        return min_max(slqueued)
    except ValueError as error:
        return 0


# ====================================================

def trunks(Agents, CallsPerHour, AHT):
    try:
        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        server = Agents
        utilisation = trafficrate / server if trafficrate < server else 0.99
        c = erlang_c(server, trafficrate)
        answertime = c / (server * deathrate * (1 - utilisation))
        secanstime = int(answertime * TIMEINTERVAL + 0.5)
        r = birthrate / (TIMEINTERVAL / (AHT + secanstime))
        ntrunks = number_trunks(server, r)
        trunks = 1 if ntrunks < 1 and trafficrate > 0 else ntrunks
        return trunks
    except ValueError as error:
        return 0


# ====================================================

def utilisation(Agents, CallsPerHour, AHT):
    try:

        birthrate = CallsPerHour
        deathrate = TIMEINTERVAL / AHT
        trafficrate = birthrate / deathrate
        utilisation = trafficrate / Agents
        return min_max(utilisation)
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
