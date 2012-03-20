from numpy import *
import wave
import struct
from random import randint, random, choice
import threading
import Queue

TARGET = None  #all ints
numframes = -1



def readTarget(targetFilename = "apollo_11_short.wav"):
    global TARGET
    global numframes
    
    wavf = wave.open(targetFilename)
    numframes = wavf.getnframes()
    numchannels =  wavf.getnchannels()
    data = wavf.readframes(numframes)
    out = struct.unpack_from ("%dh" % numframes * numchannels ,data)
    TARGET = array(out)





class Tone:
    def __init__(self, amp=None, freq=None, phase=None, start=None, dur=None):
        if amp == None:
            self.amp = random()
        else:
            self.amp = amp
            
        if freq == None:
            self.freq = randint(20,20000)
        else:
            self.freq = freq
            
        if phase == None:
            self.phase = randint(-1,1)
        else:
            self.phase = phase
            
        if start == None:
            self.start = randint(0, numframes)
        else:
            self.start = start

        if dur == None:
            self.dur = randint(0, numframes - self.start)
        else:
            self.dur = dur


    def mutate(self):
        toMutate = choice(["amp", "freq", "phase", "start", "dur"])
        direction = choice([-1,1])
        oldVal = self.__dict__[toMutate]
        oldVal += direction * 0.02 * oldVal
        self.__dict__[toMutate] = oldVal
        
        
        



class Chromosome:
    def __init__(self, length = 1000, tones=None):
        if tones == None:
            self.tones = [Tone() for _ in range(length)]
        else:
            self.tones = tones
        self.realized = False
        self.fitness = None
        self.isBest = False
        
        
    def realize(self):
        if self.realized:
            return
            
        self.value = zeros(numframes, int16)
        for tone in self.tones:
            for i in xrange(tone.start, tone.start + tone.dur):
                self.value[i] += 16384 * tone.amp * sin((2 * pi * tone.freq * i) + tone.phase)
            
            
    def mutate(self, rate = 0.05):
        """The best chromosome doesn't mutate"""
        if self.isBest:
            self.isBest = False
            return
        
        for tone in self.tones:
            if random() < rate:
                tone.mutate()
        
        
    def crossOver(self, other):
        low = int(self.length * 0.02)
        high = int(self.length * 0.08)
        cpoint = randint( low, high)
        newTones = []
        newTones.extend( self.tones[:cpoint] )
        newTones.extend( other.tones[cpoint:] )
        assert( len(newTones)  == self.length)
        
        return Chromosome(length, newTones)
        
        
    def getFitness(self):
        global TARGET
        
        """Fitness is just the euclidean distance between this and the target"""
        if not self.realized:
            self.realize()
            
        self.fitness = linalg.norm(self.value - TARGET)
        
    def __cmp__(self, other):
        if not self.fitness:
            self.getFitness()
            
        if not other.fitness:
            other.getFitness()
            
        return cmp(self.fitness, other.fitness)
        


class Realizer(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        
    def run(self):
        while True:
            chrome = self.queue.get()
            chrome.realize()
            
            self.queue.task_done()
    



class SoundFile:
   def  __init__(self, signal):
       self.file = wave.open('test.wav', 'wb')
       self.signal = signal
       self.sr = 44100

   def write(self):
       self.file.setparams((1, 2, self.sr, 44100*4, 'NONE', 'noncompressed'))
       self.file.writeframes(self.signal)
       self.file.close()



    
    
class GA:
    def __init__(self, numChromosomes=50, maxGenerations=1000):
        self.chromes = [Chromosome() for _ in xrange(numChromosomes)]
        self.maxGenerations = maxGenerations
        
    def run(self):
        queue = Queue.Queue()
        
        bestFitness = 10**10
        
        for generation in xrange(self.maxGenerations):
            print "Generation ", generation
            
            for _ in range(16):
                t = Realizer(queue)
                t.setDaemon(True)
                t.start()
                
            for chrome in self.chromes:
                queue.put(chrome)
                
            queue.join()
            
            self.chromes.sort()
            best = self.chromes[0]
            
            if best.fitness < bestFitness:
                bestFitness = best.fitness
            else:
                print "Stopping at generation", generation, "with fitness", best.fitness
                break
            
            best.isBest = True
            print "Best's fitness", best.fitness
            map(lambda t: t.mutate(), self.chromes)
            self.chromes = [t.crossover(best) for t in self.chromes]
            
            
        self.chromes.sort()
        best = self.chromes[0]
        ssignal = ''
        for i in range(len(signal)):
           ssignal += wave.struct.pack('h',signal[i]) # transform to binary


        f = SoundFile(ssignal)
        f.write()
        print 'file written'

    
    
if __name__ == "__main__":
    readTarget()
    x = GA()
    x.run()
    

