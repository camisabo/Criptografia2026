from music21 import converter, note, chord
import json

score = converter.parse("./Partituras/canon_perpetuus_per_giusti_intervalii.mxl")


def get_clef_reference_pitch(element):
    clef_context = element.getContextByClass("Clef")

    if clef_context is None:
        return "G4"

    return {
        "G": "G4",
        "F": "F3",
        "C": "C4"
    }.get(clef_context.sign, "G4")


def get_staff_position(element):
    reference_pitch = note.Note(get_clef_reference_pitch(element)).pitch
    return element.pitch.diatonicNoteNum - reference_pitch.diatonicNoteNum


def get_alteration(pitch):
    if pitch.accidental is None:
        return 0

    return int(pitch.accidental.alter)


def get_part_clef(part):
    clefs = list(part.recurse().getElementsByClass("Clef"))

    if not clefs:
        return None

    clef = clefs[0]
    return {
        "sign": clef.sign,
        "line": clef.line
    }


def get_part_key_signature(part):
    key_signatures = list(part.recurse().getElementsByClass("KeySignature"))

    if not key_signatures:
        return None

    key_signature = key_signatures[0]
    key_value = key_signature.asKey()

    return {
        "sharps": key_signature.sharps,
        "key": key_value.name if key_value is not None else None
    }


result = []

for part_index, part in enumerate(score.parts, start=1):
    part_data = {
        "part": part_index,
        "clef": get_part_clef(part),
        "key_signature": get_part_key_signature(part),
        "measures": []
    }

    sequence_position = 1

    for measure in part.getElementsByClass("Measure"):
        measure_data = {
            "measure": measure.number,
            "notes": []
        }

        for element in measure.recurse().notesAndRests:
            if isinstance(element, note.Note):
                note_data = {
                    "note": element.pitch.step,
                    "alteration": get_alteration(element.pitch),
                    "figure": element.duration.type,
                    "duration": float(element.duration.quarterLength),
                    "measure": measure.number,
                    "position": sequence_position,
                    "staff_position": get_staff_position(element)
                }

                if element.tie:
                    note_data["tie"] = element.tie.type

                if element.duration.tuplets:
                    note_data["tuplet"] = True

                measure_data["notes"].append(note_data)
                sequence_position += 1

            elif isinstance(element, note.Rest):
                measure_data["notes"].append({
                    "type": "rest",
                    "note": None,
                    "alteration": 0,
                    "figure": element.duration.type,
                    "duration": float(element.duration.quarterLength),
                    "measure": measure.number,
                    "position": sequence_position,
                    "staff_position": None
                })
                sequence_position += 1

            elif isinstance(element, chord.Chord):
                measure_data["notes"].append({
                    "type": "chord",
                    "notes": [pitch.step for pitch in element.pitches],
                    "alterations": [get_alteration(pitch) for pitch in element.pitches],
                    "figure": element.duration.type,
                    "duration": float(element.duration.quarterLength),
                    "measure": measure.number,
                    "position": sequence_position,
                    "staff_position": [pitch.diatonicNoteNum - note.Note(get_clef_reference_pitch(element)).pitch.diatonicNoteNum for pitch in element.pitches]
                })

                if element.duration.tuplets:
                    measure_data["notes"][-1]["tuplet"] = True

                sequence_position += 1

        part_data["measures"].append(measure_data)

    result.append(part_data)

with open("./Partituras/canon_perpetuus_per_giusti_intervalii.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("JSON generado correctamente.")