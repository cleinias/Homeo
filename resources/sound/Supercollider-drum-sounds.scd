# A collection of four drumkit-like sounds from
# RumbleSan Heavy Noise Industries
# http://rumblesan.com/blog/2010/10/12/drum-sounds-in-supercollider-part-1/ (and part-2)


(
    SynthDef('fullkickdrum', {

    var subosc, subenv, suboutput, clickosc, clickenv, clickoutput;

    subosc = {SinOsc.ar(60)};
    subenv = {Line.ar(1, 0, 1, doneAction: 2)};

    clickosc = {LPF.ar(WhiteNoise.ar(1),1500)};
    clickenv = {Line.ar(1, 0, 0.02)};

    suboutput = (subosc * subenv);
    clickoutput = (clickosc * clickenv);

    Out.ar(0,
        Pan2.ar(suboutput + clickoutput, 0)
    )

}).store;
)

(
SynthDef('openhat', {

    var hatosc, hatenv, hatnoise, hatoutput;

    hatnoise = {LPF.ar(WhiteNoise.ar(1),6000)};

    hatosc = {HPF.ar(hatnoise,2000)};
    hatenv = {Line.ar(1, 0, 0.3)};

    hatoutput = (hatosc * hatenv);

    Out.ar(0,
    Pan2.ar(hatoutput, 0)
    )

}).send(s);

SynthDef('closedhat', {

    var hatosc, hatenv, hatnoise, hatoutput;

    hatnoise = {LPF.ar(WhiteNoise.ar(1),6000)};

    hatosc = {HPF.ar(hatnoise,2000)};
    hatenv = {Line.ar(1, 0, 0.1)};

    hatoutput = (hatosc * hatenv);

    Out.ar(0,
    Pan2.ar(hatoutput, 0)
    )

}).send(s);
)

(
SynthDef('snaredrum', {

var drumosc, filterenv, volenv, drumoutput, snaposc, snapenv, fulloutput;

drumosc = {Pulse.ar(100)};
filterenv = {Line.ar(1, 0, 0.2, doneAction: 0)};
volenv = {Line.ar(1, 0, 0.6, doneAction: 2)};
drumoutput = {LPF.ar(drumosc,(filterenv *1000) + 30)};

snaposc = {BPF.ar(HPF.ar(WhiteNoise.ar(1),500),1500)};
snapenv = {Line.ar(1, 0, 0.2, doneAction: 0)};

fulloutput = (drumoutput * volenv) + (snaposc * snapenv);
//fulloutput = (drumoutput * volenv);

Out.ar(0,
Pan2.ar(fulloutput, 0)
)

}).send(s);
)


(
SynthDef('clap', {

var claposc, clapenv, clapnoise, clapoutput;

clapnoise = {BPF.ar(LPF.ar(WhiteNoise.ar(1),7500),1500)};
clapenv = {Line.ar(1, 0, 0.6, doneAction: 2)};

clapoutput = {Mix.arFill(7,
{arg i;
EnvGen.ar(
Env.new(
[0,0,1,0],
[0.01 * i,0,0.04]
)
) * clapnoise * 0.5
}
)};

Out.ar(0,
Pan2.ar(clapoutput * clapenv, 0)
)

}).send(s);
)


t = Synth('fullkickdrum');
o = Synth('openhat');
c = Synth('closedhat');
t = Synth('snaredrum');
t = Synth('clap');
