import random
from midiutil import MIDIFile
from datetime import datetime

class Note:
    def __init__(self, pitch, duration):
        self.pitch = pitch
        self.duration = duration

interval_values = [0, 3, 2, 1, 1, 2, 2, 0, 1, 1, 2, 3]

def generate_melody(length, min_pitch, max_pitch, allowed_intervals, allowed_durations, **kwargs):
    melody = []
    complete = False
    while not complete:
        # Compile list of possible durations (excluding durations that would exceed desired melody length).
        possible_durations = []
        for duration in allowed_durations:
            if duration <= length - calc_melody_length(melody):
                possible_durations.append(duration)
        # If there is no possible durations, the melody is complete.
        if len(possible_durations) == 0:
            complete = True
            break
        # Choose a random duration for the note.
        chosen_duration = random.choice(possible_durations)
        # Compile list of possible pitches (excluding pitches that exceed min_pitch or max_pitch).
        possible_pitches = []
        if len(melody) == 0:
            possible_pitches.append(min_pitch)
        else: 
            for interval in allowed_intervals:
                above = melody[-1].pitch + interval
                below = melody[-1].pitch - interval
                if above < max_pitch:
                    possible_pitches.append(above)
                if below > min_pitch:
                    possible_pitches.append(below)
        chosen_pitch = random.choice(possible_pitches)
        # If a melody-to-counter is provided, pitches are ranked by the intervals they create against it.
        melody_to_counter = kwargs.get("melody_to_counter")
        if  melody_to_counter:
            # Calculate note timespan
            if len(melody) == 0:
                note_timespan = {"start_time": 0, "end_time": chosen_duration}
            else:
                prev_note_end_time = get_timespan_of_note_in_melody(melody, len(melody) - 1)["end_time"]
                note_timespan = {"start_time": prev_note_end_time, "end_time": prev_note_end_time + chosen_duration}
            # Get overlapped notes in the melody-to-counter.
            overlapped_notes = get_notes_in_timespan(melody_to_counter, note_timespan)
            # If crossover of melody and melody-to-counter is not allowed, remove any pitches that would do this.
            if kwargs.get("allow_crossover") == False:
                melody_is_above = min_pitch > melody_to_counter[0].pitch
                for pp in possible_pitches:
                    for note in overlapped_notes:
                        if melody_is_above and pp < note.pitch or not melody_is_above and pp > note.pitch:
                            possible_pitches.remove(pp)
                            print("removed pitch")
            # Rank possible pitches.
            print(len(possible_pitches))
            pitches_ranked = {}
            for pp in possible_pitches:
                score = 0
                for note in overlapped_notes:
                    score += interval_values[get_interval_between_pitches(pp, note.pitch)]
                if len(overlapped_notes) != 0:
                    score = score / len(overlapped_notes) # Get the mean.
                pitches_ranked[pp] = score
            # Pick between highest ranked pitches.
            print(pitches_ranked)
            best_pitches = []
            highest_score = -1
            for pitch in pitches_ranked.keys():
                score = pitches_ranked[pitch]
                if score > highest_score:
                    best_pitches = [pitch]
                    highest_score = score
                elif score == highest_score:
                    best_pitches.append(pitch)
            chosen_pitch = random.choice(best_pitches)
        # Generate note from chosen pitch and duration and add to melody.
        melody.append(Note(chosen_pitch, chosen_duration))
    return melody

def calc_melody_length(melody):
    length = 0
    for note in melody:
        length += note.duration
    return length

note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def get_note_name(note):
    note_name = note_names[note.pitch % 12]
    octave = int(note.pitch / 12)
    return f"{note_name}{octave}"

def get_notes_in_timespan(melody, timespan):
    notes = []
    # print("timespan: " + str(timespan))
    for i in range(0, len(melody) - 1):
        ts = get_timespan_of_note_in_melody(melody, i)
        # print("ts: " + str(ts))
        if ts["start_time"] >= timespan["start_time"] and ts["end_time"] <= timespan["start_time"] or ts["start_time"] >= timespan["end_time"] and ts["end_time"] <= timespan["end_time"] or ts["start_time"] >= timespan["start_time"] and ts["end_time"] <= timespan["end_time"] or ts["start_time"] <= timespan["start_time"] and ts["end_time"] >= timespan["end_time"]:
            notes.append(melody[i])
            # print("Overlap!")
    return notes
        
def get_timespan_of_note_in_melody(melody, note_index): # Get the timespan of the note at the given index in the given melody.
    # Calculate start time as the sum of the previous notes' durations.
    start_time = 0
    for i in range(0, note_index - 1):
        start_time += melody[i].duration
    # Calculate end time by adding note duration to start time.
    end_time = start_time + melody[note_index].duration
    return {"start_time": start_time, "end_time": end_time}

def get_interval_between_pitches(p1, p2):
    return abs(p1 % 12 - p2 % 12)

melody = generate_melody(32, 0, 87, [1, 2, 6, 10, 11], [4])
counter_melody = generate_melody(32, 6, 87, [1, 2, 6, 10, 11], [4], melody_to_counter=melody, allow_crossover=False)
channels = [counter_melody, melody]

print([get_note_name(note) for note in melody])
print([get_note_name(note) for note in counter_melody])

track = 0
time = 0

mf = MIDIFile(1)
mf.addTrackName(track, time, "Track 1")
mf.addTempo(track, time, 60)
for i in range(0, len(channels)):
    time = 0
    for note in channels[i]:
        mf.addNote(track, i, note.pitch, time, note.duration, 64)
        time += note.duration
timestr = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
with open(f"{timestr}.mid", "wb") as outf:
   mf.writeFile(outf)