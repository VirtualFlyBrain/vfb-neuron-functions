#!/usr/bin/env python3
"""Map known_function and category values to GO/NBO ontology terms."""

import csv
import re
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = str(ROOT / 'neuron_functions.tsv')
OUTPUT = str(ROOT / 'neuron_functions.tsv')

# --- Curated mapping: normalised function term → (ontology_id, label) ---
# GO Biological Process preferred; NBO as fallback.

FUNCTION_MAP = {
    # === Broad categories ===
    'visual': ('GO:0007632', 'visual behavior'),
    'olfactory': ('GO:0042048', 'olfactory behavior'),
    'gustatory': ('GO:0050909', 'sensory perception of taste'),
    'chemosensory': ('GO:0007635', 'chemosensory behavior'),
    'learning_and_memory': ('GO:0007611', 'learning or memory'),
    'learning': ('GO:0007612', 'learning'),
    'memory': ('GO:0007613', 'memory'),
    'reproduction': ('GO:0000003', 'reproduction'),
    'movement': ('GO:0040011', 'locomotion'),
    'walking': ('GO:0007628', 'adult walking behavior'),
    'flight': ('GO:0007629', 'flight behavior'),
    'feeding': ('GO:0007631', 'feeding behavior'),
    'grooming': ('GO:0007625', 'grooming behavior'),
    'thermosensory': ('GO:0040040', 'thermosensory behavior'),
    'hygrosensory': ('GO:0098509', 'sensory perception of humidity'),
    'circadian_rhythm': ('GO:0007623', 'circadian rhythm'),
    'navigation': ('GO:0007626', 'locomotory behavior'),
    'nociception': ('GO:0019233', 'sensory perception of pain'),
    # 'neuromodulatory' - too vague, skip
    'mechanosensory': ('GO:0007638', 'mechanosensory behavior'),

    # === Visual system ===
    'visual_vertical_widefieldmotion': ('GO:0007601', 'visual perception'),
    'visual_horizontal_widefieldmotion': ('GO:0007601', 'visual perception'),
    'visual_horizontal_widefield motion': ('GO:0007601', 'visual perception'),
    'horizontal flow': ('GO:0007601', 'visual perception'),
    'vertical flow': ('GO:0007601', 'visual perception'),
    'visual_small_object': ('GO:0007632', 'visual behavior'),
    'visual_large_objects': ('GO:0007632', 'visual behavior'),
    'visual_thin_vertical_bar': ('GO:0007632', 'visual behavior'),
    'visual_loom': ('GO:0007632', 'visual behavior'),
    'visual_chromatic': ('GO:0007601', 'visual perception'),
    'visual_polarized_light': ('GO:0007601', 'visual perception'),
    'stripe-selective': ('GO:0007632', 'visual behavior'),
    'orientation selective': ('GO:0007632', 'visual behavior'),
    'motion selective': ('GO:0007632', 'visual behavior'),
    'off responsive': ('GO:0007601', 'visual perception'),
    'off motion detector': ('GO:0007601', 'visual perception'),
    'on motion input': ('GO:0007601', 'visual perception'),
    'off motion input': ('GO:0007601', 'visual perception'),
    'off motion support': ('GO:0007601', 'visual perception'),
    'on fast input': ('GO:0007601', 'visual perception'),
    'off fast input': ('GO:0007601', 'visual perception'),
    'on delayed input': ('GO:0007601', 'visual perception'),
    'off delayed input': ('GO:0007601', 'visual perception'),
    'on inhibitory': ('GO:0007601', 'visual perception'),
    'off excitatory': ('GO:0007601', 'visual perception'),
    'sustained input': ('GO:0007601', 'visual perception'),
    'off sustained input': ('GO:0007601', 'visual perception'),
    'on front-to-back motion': ('GO:0007601', 'visual perception'),
    'on back-to-front motion': ('GO:0007601', 'visual perception'),
    'on upward motion': ('GO:0007601', 'visual perception'),
    'on downward motion': ('GO:0007601', 'visual perception'),
    'non-linear amplification of dim stimuli': ('GO:0007601', 'visual perception'),
    'achromatic vision': ('GO:0007601', 'visual perception'),
    'uv selective': ('GO:0009589', 'detection of UV'),
    'uv detection': ('GO:0009589', 'detection of UV'),
    'uv pooling': ('GO:0009589', 'detection of UV'),
    'polarized uv detection': ('GO:0009589', 'detection of UV'),
    'uv': ('GO:0009589', 'detection of UV'),
    'blue selective': ('GO:0007601', 'visual perception'),
    'blue detection': ('GO:0007601', 'visual perception'),
    'green detection': ('GO:0007601', 'visual perception'),
    'color opponent': ('GO:0007601', 'visual perception'),
    'phototaxis': ('GO:0042331', 'phototaxis'),
    'circadian photosensitivity': ('GO:0007623', 'circadian rhythm'),
    'ocellar': ('GO:0007601', 'visual perception'),
    'looming detector': ('GO:0007632', 'visual behavior'),
    'respond to looming stimuli': ('GO:0007632', 'visual behavior'),
    'collision avoidance': ('NBO:0040005', 'visually guided collision avoidance behavior'),
    'looming escape': ('NBO:0040003', 'escape behavior'),
    'small object detection': ('GO:0007632', 'visual behavior'),
    'small object': ('GO:0007632', 'visual behavior'),
    'steer object towards midline': ('GO:0007632', 'visual behavior'),
    'ipsilateral vertical bar detection': ('GO:0007632', 'visual behavior'),
    'frontal visual field object detection': ('GO:0007632', 'visual behavior'),
    'lateral visual field object detection': ('GO:0007632', 'visual behavior'),
    'electrical synapses for object tracking in flight': ('GO:0007632', 'visual behavior'),
    'complex line motion': ('GO:0007632', 'visual behavior'),
    'visual motion in flight': ('GO:0007632', 'visual behavior'),
    'saccadic orientation towards landscape features during flight': ('GO:0007632', 'visual behavior'),
    'forward motion': ('GO:0007632', 'visual behavior'),
    'backward walking': ('GO:0043057', 'backward locomotion'),

    # === Olfactory system ===
    'decaying_fruit': ('GO:0042048', 'olfactory behavior'),
    'yeasty': ('GO:0042048', 'olfactory behavior'),
    'fruity': ('GO:0042048', 'olfactory behavior'),
    'dangerous': ('GO:0042048', 'olfactory behavior'),
    'alcoholic_fermentation': ('GO:0042048', 'olfactory behavior'),
    'acid sensing': ('GO:0042048', 'olfactory behavior'),
    'plant_matter': ('GO:0042048', 'olfactory behavior'),
    'animal_matter': ('GO:0042048', 'olfactory behavior'),
    'yeasty/fruity': ('GO:0042048', 'olfactory behavior'),
    'yeasty/fruity/dangerous': ('GO:0042048', 'olfactory behavior'),
    'yeasty/plant_matter': ('GO:0042048', 'olfactory behavior'),
    'fruity/dangerous': ('GO:0042048', 'olfactory behavior'),
    'dangerous/plant_matter': ('GO:0042048', 'olfactory behavior'),
    'unknown/dangerous': ('GO:0042048', 'olfactory behavior'),
    'decaying_fruit/plant_matter': ('GO:0042048', 'olfactory behavior'),
    'decaying_fruit/animal_matter': ('GO:0042048', 'olfactory behavior'),
    'alcoholic_fermentation/dangerous/plant_matter': ('GO:0042048', 'olfactory behavior'),
    'alcoholic_fermentation/fruity': ('GO:0042048', 'olfactory behavior'),
    'alcoholic_fermentation/yeasty': ('GO:0042048', 'olfactory behavior'),
    'aversion': ('GO:0042048', 'olfactory behavior'),
    'aversive': ('GO:0008306', 'associative learning'),
    'attraction': ('GO:0042048', 'olfactory behavior'),
    'aversive odour': ('GO:0042048', 'olfactory behavior'),
    'aversive odour processing': ('GO:0042048', 'olfactory behavior'),
    'not aversive odour avoidance': ('GO:0042048', 'olfactory behavior'),
    'respond to fly odour': ('GO:0042048', 'olfactory behavior'),
    'detect fly odour methyl laurate': ('GO:0042048', 'olfactory behavior'),
    'geosmin avoidance': ('GO:0042048', 'olfactory behavior'),
    'geosmin sensing': ('GO:0042048', 'olfactory behavior'),
    'bacterial metabolite indole detection': ('GO:0042048', 'olfactory behavior'),
    'citrus fruit detection for selective oviposition': ('GO:0042048', 'olfactory behavior'),
    'vinegar attraction': ('GO:0042048', 'olfactory behavior'),
    'attraction in both sexes': ('GO:0042048', 'olfactory behavior'),
    'phasic co2 response': ('GO:0042048', 'olfactory behavior'),
    'co2 attraction': ('GO:0042048', 'olfactory behavior'),
    'co2 aversion': ('GO:0042048', 'olfactory behavior'),
    'respond to co2': ('GO:0042048', 'olfactory behavior'),
    'acid or high concentration co2 aversion': ('GO:0042048', 'olfactory behavior'),
    'intra-glomerular gain control': ('GO:0042048', 'olfactory behavior'),
    'presynaptic global gain control': ('GO:0042048', 'olfactory behavior'),
    'postsynaptic pn inhibition': ('GO:0042048', 'olfactory behavior'),
    'negative covariance with odour valence': ('GO:0042048', 'olfactory behavior'),
    'positive covariance with odour valence': ('GO:0042048', 'olfactory behavior'),
    'scale odour-evoked run length': ('GO:0042048', 'olfactory behavior'),
    'integrate leucokinin-dependent hunger signals with food odours to suppress nociceptive avoidance (fb2b) and favour food seeking': ('GO:0042048', 'olfactory behavior'),
    'increase left-right contrast in da1_lpn': ('GO:0042048', 'olfactory behavior'),
    'sensitizes olfactory signaling': ('GO:0042048', 'olfactory behavior'),

    # === Pheromone ===
    'pheromone': ('GO:0019236', 'response to pheromone'),
    'pheromones': ('GO:0019236', 'response to pheromone'),
    'contact pheromone sensation': ('GO:0019236', 'response to pheromone'),
    'cva male pheromone detection': ('GO:0019236', 'response to pheromone'),
    'cva male pheromone': ('GO:0019236', 'response to pheromone'),
    'rate of change of cva concentration': ('GO:0019236', 'response to pheromone'),
    'sex pheromone of the parasitic wasp l.boulardi': ('GO:0019236', 'response to pheromone'),

    # === Learning and memory ===
    'appetitive_learning': ('GO:0008306', 'associative learning'),
    'appetitive': ('GO:0008306', 'associative learning'),
    'aversive memory retrieval': ('GO:0007613', 'memory'),
    'innate olfactory approach': ('GO:0042048', 'olfactory behavior'),
    'aversive memory': ('GO:0007613', 'memory'),
    'appetitive_learning; sweet taste through octopamine for short-term memory': ('GO:0008306', 'associative learning'),
    'sweet taste through octopamine for short-term memory': ('GO:0008306', 'associative learning'),
    'sufficnet for long-term memory of odour when hungry': ('GO:0007613', 'memory'),
    'nutrient-dependent long-term memory': ('GO:0007613', 'memory'),
    'innate electric shock avoidance': ('NBO:0000635', 'avoidance behavior'),

    # === Gustatory ===
    'bitter taste': ('GO:0050913', 'sensory perception of bitter taste'),
    'sweet taste': ('GO:0050916', 'sensory perception of sweet taste'),
    'labellar bristle gustatory receptor neuron': ('GO:0050909', 'sensory perception of taste'),
    'pharyngeal gustatory recetor neurons': ('GO:0050909', 'sensory perception of taste'),
    'taste peg gustatory receptor neuron': ('GO:0050909', 'sensory perception of taste'),
    'dorsal taste peg gustatory receptor neuron': ('GO:0050909', 'sensory perception of taste'),
    'gustatory receptor neuron': ('GO:0050909', 'sensory perception of taste'),
    'gustatory': ('GO:0050909', 'sensory perception of taste'),
    'sensing carbonation & fatty acids': ('GO:0050909', 'sensory perception of taste'),
    'mild aversive response to glutamate': ('GO:0050909', 'sensory perception of taste'),
    'water-sensing': ('GO:0050909', 'sensory perception of taste'),
    'sweet-sensing': ('GO:0050916', 'sensory perception of sweet taste'),
    'sugar sensing and trigger feeding': ('GO:0050916', 'sensory perception of sweet taste'),
    'appetitive sugar and low salt responses': ('GO:0050909', 'sensory perception of taste'),
    'respond to sugar and water': ('GO:0050909', 'sensory perception of taste'),
    'respond to bitter': ('GO:0050913', 'sensory perception of bitter taste'),
    'respond to biiter': ('GO:0050913', 'sensory perception of bitter taste'),
    'high salt avoidance labellar bristle gustatory receptor neuron': ('GO:0050909', 'sensory perception of taste'),
    'labellar opening/spreading in response to attractive stimulus': ('GO:0007631', 'feeding behavior'),
    'control pharyngeal pumping': ('GO:0007631', 'feeding behavior'),
    'control the length of yeast feeding bursts': ('GO:0007631', 'feeding behavior'),
    'postingestive decision to let food pass to the crop': ('GO:0007631', 'feeding behavior'),
    'facilitate ingestion to increase yeast feeding burst length': ('GO:0007631', 'feeding behavior'),

    # === Reproduction / courtship ===
    'courtship': ('GO:0007619', 'courtship behavior'),
    'courtship promotion': ('GO:0007619', 'courtship behavior'),
    'activation promotes male courtship': ('GO:0007619', 'courtship behavior'),
    'required for optimal male copulation': ('GO:0007620', 'copulation'),
    'courtship song': ('GO:0045433', 'male courtship behavior, veined wing generated song production'),
    'sine_song': ('GO:0045433', 'male courtship behavior, veined wing generated song production'),
    'pulse_song': ('GO:0045433', 'male courtship behavior, veined wing generated song production'),
    'wing_vibration': ('GO:0016545', 'male courtship behavior, veined wing vibration'),
    'courtship behavioural motif': ('GO:0007619', 'courtship behavior'),
    'singing': ('GO:0045433', 'male courtship behavior, veined wing generated song production'),
    'pulse song production': ('GO:0045433', 'male courtship behavior, veined wing generated song production'),
    'prothoracic song neuron': ('GO:0045433', 'male courtship behavior, veined wing generated song production'),
    'may encode the courtship song inter-pulse-interval': ('GO:0045433', 'male courtship behavior, veined wing generated song production'),
    'regulator of wing extension and cycles per pulse of courtship song': ('GO:0045433', 'male courtship behavior, veined wing generated song production'),
    'oviposition': ('GO:0018991', 'egg-laying behavior'),
    'egg_laying': ('GO:0018991', 'egg-laying behavior'),
    'abdomen_curl': ('GO:0018991', 'egg-laying behavior'),
    'vaginal_plate_opening': ('GO:0018991', 'egg-laying behavior'),
    'uterine_contraction': ('GO:0006936', 'muscle contraction'),
    'mating_status': ('GO:0007617', 'mating behavior'),
    'aggression': ('GO:0002118', 'aggressive behavior'),

    # === Locomotion / walking ===
    'forward': ('GO:0007628', 'adult walking behavior'),
    'forward; walking': ('GO:0007628', 'adult walking behavior'),
    'backwards walking': ('GO:0043057', 'backward locomotion'),
    'backwards': ('GO:0043057', 'backward locomotion'),
    'backward-jumping': ('GO:0043057', 'backward locomotion'),
    'forward-jumping': ('GO:0040011', 'locomotion'),
    'turning': ('GO:0035178', 'turning behavior'),
    'turning; lower speed; odour-evoked offset search': ('GO:0035178', 'turning behavior'),
    'lower speed': ('GO:0007628', 'adult walking behavior'),
    'odour-evoked offset search': ('GO:0042048', 'olfactory behavior'),
    'slowing & turning': ('GO:0035178', 'turning behavior'),
    'stride': ('GO:0007628', 'adult walking behavior'),
    'bidirectional regulation of walking speed': ('GO:0007628', 'adult walking behavior'),
    'increase forward velocity': ('GO:0007628', 'adult walking behavior'),
    'rhythmic leg movements': ('GO:0007628', 'adult walking behavior'),
    'shorten stride of the inside leg': ('GO:0007628', 'adult walking behavior'),
    'lengthen stride of outside leg': ('GO:0007628', 'adult walking behavior'),
    'halting': ('GO:0007628', 'adult walking behavior'),
    'rest': ('GO:0030431', 'sleep'),
    'backing up': ('GO:0043057', 'backward locomotion'),
    'retreat behavior': ('GO:0043057', 'backward locomotion'),

    # === Flight ===
    'escape_takeoff': ('GO:0007629', 'flight behavior'),
    'flight_induction': ('GO:0007629', 'flight behavior'),
    'activation in flight': ('GO:0007629', 'flight behavior'),
    'wing steering': ('GO:0007629', 'flight behavior'),
    'wing thrust': ('GO:0007629', 'flight behavior'),
    'lift': ('GO:0007629', 'flight behavior'),
    'pitch': ('GO:0007629', 'flight behavior'),
    'wing power': ('GO:0007629', 'flight behavior'),
    'wingbeat amplitude': ('GO:0007629', 'flight behavior'),
    'contralateral wingbeat amplitude': ('GO:0007629', 'flight behavior'),
    'wing beat oscillation power in flight': ('GO:0007629', 'flight behavior'),
    'flight saccade': ('GO:0007629', 'flight behavior'),
    'inhibit flight saccade': ('GO:0007629', 'flight behavior'),
    'rapid saccadic turning': ('GO:0007629', 'flight behavior'),
    'turning or saccade in flight': ('GO:0007629', 'flight behavior'),
    'landing': ('GO:0007629', 'flight behavior'),
    'ipsiversive': ('GO:0007629', 'flight behavior'),
    'ipsiversive steering': ('GO:0007629', 'flight behavior'),
    'contraversive steering': ('GO:0007629', 'flight behavior'),
    'low gain steering': ('GO:0007629', 'flight behavior'),
    'high gain steering': ('GO:0007629', 'flight behavior'),

    # === BANC supplement (BANC_function_supplement.tsv) ===
    # Bare "steering" applies to both walking and flight DNs, so use the
    # generic locomotory term rather than flight-specific.
    'steering': ('GO:0008344', 'adult locomotory behavior'),
    'threat_response': ('GO:0002209', 'behavioral defense response'),
    'visual_front_leg_feedback': ('GO:0007632', 'visual behavior'),

    # === Escape ===
    'freezing': ('NBO:0040003', 'escape behavior'),
    'escape response': ('NBO:0040003', 'escape behavior'),

    # === Grooming ===
    'antennal_grooming': ('GO:0007625', 'grooming behavior'),
    'antennal grooming': ('GO:0007625', 'grooming behavior'),
    'front leg rubbing': ('GO:0007625', 'grooming behavior'),
    'inhibit dng11 front leg rubbing': ('GO:0007625', 'grooming behavior'),
    'abdomen grooming': ('GO:0007625', 'grooming behavior'),
    'backward motion followed by grooming': ('GO:0007625', 'grooming behavior'),
    'detect leg movements during head grooming': ('GO:0007625', 'grooming behavior'),

    # === Proboscis / feeding motor ===
    'proboscis_extension': ('GO:0007637', 'proboscis extension reflex'),
    'control proboscis positioning': ('GO:0007637', 'proboscis extension reflex'),
    'control proboscis positioning: haustellum extension': ('GO:0007637', 'proboscis extension reflex'),
    'control proboscis positioning: labellar extension': ('GO:0007637', 'proboscis extension reflex'),
    'control proboscis positioning: rostrum protraction': ('GO:0007637', 'proboscis extension reflex'),
    'control salivation': ('GO:0046541', 'saliva secretion'),

    # === Motor / neck ===
    'neck_motor': ('GO:0040011', 'locomotion'),
    'neck motor': ('GO:0040011', 'locomotion'),
    'neck_control': ('GO:0040011', 'locomotion'),
    'haltere': ('GO:0007629', 'flight behavior'),
    'gaze stabilization': ('GO:0007632', 'visual behavior'),
    'pitch head downward 10-15 degrees': ('NBO:0000020', 'head movement'),
    'ventral head sweeps': ('NBO:0000020', 'head movement'),
    'motor': ('GO:0040011', 'locomotion'),
    'leg': ('GO:0040011', 'locomotion'),
    'abdomen_motion': ('GO:0040011', 'locomotion'),
    'wing': ('GO:0040011', 'locomotion'),
    'mesothoracic': ('GO:0040011', 'locomotion'),
    'prosternal': ('GO:0040011', 'locomotion'),
    'notum': ('GO:0040011', 'locomotion'),

    # === Hearing / mechanosensory ===
    'high frequency sound': ('GO:0007605', 'sensory perception of sound'),
    'low frequency sound': ('GO:0007605', 'sensory perception of sound'),
    'vibration and static deflection of antennal receiver': ('GO:0007638', 'mechanosensory behavior'),
    'jo-e static deflection (pull) of antenna': ('GO:0007638', 'mechanosensory behavior'),
    'static deflection (pull) of antenna': ('GO:0007638', 'mechanosensory behavior'),
    'static deflection (push) of antenna': ('GO:0007638', 'mechanosensory behavior'),
    'activation induces grooming and wing flapping': ('GO:0007638', 'mechanosensory behavior'),
    'activation induces grooming & wing flapping': ('GO:0007638', 'mechanosensory behavior'),

    # === Thermosensory / hygrosensory ===
    'thermo_hygro': ('GO:0040040', 'thermosensory behavior'),
    'thermohygro': ('GO:0040040', 'thermosensory behavior'),
    'thermo_hygro; thermosensory': ('GO:0040040', 'thermosensory behavior'),
    'rate of temperature change': ('GO:0016048', 'detection of temperature stimulus'),
    'rate of temperaure change': ('GO:0016048', 'detection of temperature stimulus'),
    'gradient of temperature change': ('GO:0016048', 'detection of temperature stimulus'),
    'sense temperature rapid change & value': ('GO:0016048', 'detection of temperature stimulus'),
    'early hot/cold avoidance': ('GO:0040040', 'thermosensory behavior'),
    'cold sensitive': ('GO:0016048', 'detection of temperature stimulus'),
    'hot sensitive': ('GO:0016048', 'detection of temperature stimulus'),
    'hot-sensing': ('GO:0016048', 'detection of temperature stimulus'),
    'cold sensing': ('GO:0016048', 'detection of temperature stimulus'),
    'absolute cold sensing': ('GO:0016048', 'detection of temperature stimulus'),
    'cold on response': ('GO:0016048', 'detection of temperature stimulus'),
    'cooling': ('GO:0016048', 'detection of temperature stimulus'),
    'adapting': ('GO:0016048', 'detection of temperature stimulus'),
    'non-adapting': ('GO:0016048', 'detection of temperature stimulus'),
    'temperature-modulated sleep regulation': ('GO:0040040', 'thermosensory behavior'),
    'humid': ('GO:0098509', 'sensory perception of humidity'),
    'humid sensing': ('GO:0098509', 'sensory perception of humidity'),
    'dry sensing': ('GO:0098509', 'sensory perception of humidity'),
    'dry-sensing': ('GO:0098509', 'sensory perception of humidity'),
    'dry': ('GO:0098509', 'sensory perception of humidity'),
    'evaporation_dry_olf': ('GO:0098509', 'sensory perception of humidity'),
    'humid_heating_olf': ('GO:0098509', 'sensory perception of humidity'),
    'humid_heating': ('GO:0098509', 'sensory perception of humidity'),
    'humid_cooling': ('GO:0098509', 'sensory perception of humidity'),
    'heating_humid': ('GO:0040040', 'thermosensory behavior'),
    'heating_unknown': ('GO:0040040', 'thermosensory behavior'),
    'heating_gustatory': ('GO:0040040', 'thermosensory behavior'),

    # === Navigation / heading ===
    'heading direction': ('GO:0007626', 'locomotory behavior'),
    'heading direction & angular velocity': ('GO:0007626', 'locomotory behavior'),
    'angular path integration': ('GO:0007626', 'locomotory behavior'),
    'allocentric goal': ('GO:0007626', 'locomotory behavior'),
    'rotational velocity': ('GO:0007626', 'locomotory behavior'),
    'compare allocentric heading vs. goal angles': ('GO:0007626', 'locomotory behavior'),

    # === Circadian ===
    'input to clock neurons': ('GO:0007623', 'circadian rhythm'),
    'i-lnv clock neuron': ('GO:0007623', 'circadian rhythm'),
    'time-of-day-dependent activity': ('GO:0007623', 'circadian rhythm'),
    'morning activity': ('GO:0007623', 'circadian rhythm'),

    # === Heart / internal ===
    'heart': ('GO:0060047', 'heart contraction'),
    # 'crop-innervating enteric motor neuron' - no specific function, skip

    # === Neuromodulatory / neuropeptide ===
    'drosophila insulin-like peptides secretion': ('GO:0030073', 'insulin secretion'),
    'enhances appetitive behaviour and food intake': ('GO:0007631', 'feeding behavior'),
    'stimulation mimics food-deprivation': ('GO:0007631', 'feeding behavior'),
    'hunger': ('GO:0007631', 'feeding behavior'),
    'thirsty water seeking': ('GO:0009414', 'response to water deprivation'),
    'water balance': ('GO:0030104', 'water homeostasis'),
    'neuropeptide f (food deprivation) receptor': ('GO:0007631', 'feeding behavior'),
    'octopamine (sweet taste) receptor': ('GO:0050916', 'sensory perception of sweet taste'),

    # === Approach / avoidance ===
    # 'drive approach' / 'activation drives approach' - too vague, skip
    'activation drives avoidance': ('NBO:0000635', 'avoidance behavior'),
    'activation: reduce groundspeed': ('GO:0007628', 'adult walking behavior'),
    'turning on unilateral activation': ('GO:0035178', 'turning behavior'),
    'forward on bilateral activation': ('GO:0007628', 'adult walking behavior'),

    # === Gustatory receptor neuron subtypes (mixed) - map the functional part ===
    'fru+/ ppk23+/ ppk25+ leg bristle local gustatory receptor neuron': ('GO:0019236', 'response to pheromone'),
    'fru-/ ir52a+/ ir52b+ leg bristle local gustatory receptor neuron': ('GO:0050909', 'sensory perception of taste'),
    'gustatory courtship-promoting fru+/ir52a+ gustatory receptor neuron': ('GO:0007619', 'courtship behavior'),
    'vglut+/ fru+/ ppk23+/ ppk25+ leg bristle local gustatory receptor neuron': ('GO:0019236', 'response to pheromone'),
    'vglut-/ fru+/ ppk23+/ ppk25- leg bristle local gustatory receptor neuron': ('GO:0019236', 'response to pheromone'),
    'vglut+/ fru+/ ppk23+/ ppk25+ gustatory receptor neuron': ('GO:0019236', 'response to pheromone'),
    'vglut-/ fru+/ ppk23+/ ppk25- gustatory receptor neuron': ('GO:0050909', 'sensory perception of taste'),
    'leg bristle local gustatory receptor neuron': ('GO:0050909', 'sensory perception of taste'),
    'leg bristle ascending gustatory receptor neuron': ('GO:0050909', 'sensory perception of taste'),
    'ir94e labellar bristle gustatory receptor neuron': ('GO:0050909', 'sensory perception of taste'),
    'gr64f sweet-sensing labellar bristle gustatory receptor neuron': ('GO:0050916', 'sensory perception of sweet taste'),
    'gr5a sugar sensing leg bristle local gustatory receptor neuron': ('GO:0050916', 'sensory perception of sweet taste'),
    'sense (bitter) aversive compounds': ('GO:0050913', 'sensory perception of bitter taste'),
    'sense appetitive tastants': ('GO:0050909', 'sensory perception of taste'),
    'sense secreted cuticular hydrocarbons to inhibit conspecific male and interspecies courtship': ('GO:0019236', 'response to pheromone'),
    'polarization sensitive neuron': ('GO:0007601', 'visual perception'),

    # === Misc specific descriptors (map to nearest parent) ===
    'r7d input to dmdra1': ('GO:0007601', 'visual perception'),
    'r8d input to dmdra2': ('GO:0007601', 'visual perception'),
    'puff': ('GO:0001964', 'startle response'),
    'sleep': ('GO:0030431', 'sleep'),

    # === Catch some that only appear as comma-separated subterms ===
    'absolute cold sensing': ('GO:0016048', 'detection of temperature stimulus'),
    'respond to fly odour': ('GO:0042048', 'olfactory behavior'),
    'attraction in both sexes': ('GO:0042048', 'olfactory behavior'),
    'attraction (lh290)': ('GO:0042048', 'olfactory behavior'),
    'detect glycerol and induce proboscis extension': ('GO:0007637', 'proboscis extension reflex'),
    'sugar sensing leg bristle local gustatory receptor neuron': ('GO:0050916', 'sensory perception of sweet taste'),
    'sweet-sensing labellar bristle gustatory receptor neuron': ('GO:0050916', 'sensory perception of sweet taste'),
}

# Molecular marker terms to skip (no functional information)
SKIP_TERMS = {
    'gr5a', 'gr64e', 'gr64f', 'gr77a', 'gr33a', 'gr32a', 'gr61a',
    'ppk28', 'ppk23', 'ir67c', 'ir60d', 'ir56d', 'ir56b', 'ir47a',
    'ir10a', 'ir100a', 'ir7c', 'ir94e', 'gr64f+/ ir56b+',
    'glutamatergic ir7c',
    '(59 (w)',
    '30 (h)) degrees visual receptive field',
    'neuromodulatory (dnpf)',
    'neuromodulatory',
    'crop-innervating entiric motor neuron',
    'drive approach',
    'activation drives approach',
}


def split_function_terms(kf_string):
    """Split a known_function string into individual terms.
    Splits on semicolons first, then on commas within each part.
    Returns a list of stripped, non-empty terms.
    """
    terms = []
    for part in re.split(r';\s*', kf_string):
        # Split on commas, but not inside parentheses
        subparts = re.split(r',\s*(?![^()]*\))', part)
        for sp in subparts:
            sp = sp.strip()
            if sp:
                terms.append(sp)
    return terms


def normalise_term(term):
    """Normalise a function term for lookup."""
    t = term.strip().lower()
    # Remove leading gene names like "Gr64e (detect...)" → keep the description
    m = re.match(r'^[a-z]{2,4}\d+[a-z]?\s*\((.+)\)$', t)
    if m:
        t = m.group(1)
    # Remove leading gene names followed by space and description
    m = re.match(r'^[a-z]{2,4}\d+[a-z]?\s+(.+)$', t)
    if m and not t.startswith('jo-'):
        t = m.group(1)
    return t.strip()


def ols_search_go(query, page_size=3):
    """Search GO for a term."""
    params = urllib.parse.urlencode({'q': query, 'ontology': 'go', 'type': 'class', 'rows': page_size})
    url = f'https://www.ebi.ac.uk/ols4/api/search?{params}'
    time.sleep(0.35)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
    except:
        return []
    results = []
    for doc in data.get('response', {}).get('docs', []):
        obo_id = doc.get('obo_id', '')
        label = doc.get('label', '')
        if obo_id and obo_id.startswith('GO:'):
            results.append((obo_id, label))
    return results


def ols_search_nbo(query, page_size=3):
    """Search NBO for a term."""
    params = urllib.parse.urlencode({'q': query, 'ontology': 'nbo', 'type': 'class', 'rows': page_size})
    url = f'https://www.ebi.ac.uk/ols4/api/search?{params}'
    time.sleep(0.35)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
    except:
        return []
    results = []
    for doc in data.get('response', {}).get('docs', []):
        obo_id = doc.get('obo_id', '')
        label = doc.get('label', '')
        if obo_id and obo_id.startswith('NBO:'):
            results.append((obo_id, label))
    return results


def main():
    with open(INPUT, newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Strip existing columns from previous runs
    fieldnames = [fn for fn in fieldnames if fn not in ('function_ont_id', 'function_ont_label')]
    for row in rows:
        row.pop('function_ont_id', None)
        row.pop('function_ont_label', None)
        row.pop('', None)

    print(f"Read {len(rows)} rows", file=sys.stderr)

    # Collect all unique normalised function terms
    all_terms = set()
    for row in rows:
        kf = row['known_function'].strip()
        if kf:
            for part in split_function_terms(kf):
                norm = normalise_term(part)
                if norm:
                    all_terms.add(norm)

    print(f"Unique normalised terms: {len(all_terms)}", file=sys.stderr)

    # Check which terms are in the curated map
    mapped = set()
    unmapped = set()
    skipped = set()
    for t in all_terms:
        if t in SKIP_TERMS:
            skipped.add(t)
        elif t in FUNCTION_MAP:
            mapped.add(t)
        else:
            unmapped.add(t)

    print(f"Curated map hits: {len(mapped)}", file=sys.stderr)
    print(f"Skipped (molecular only): {len(skipped)}", file=sys.stderr)
    print(f"Unmapped (need OLS search): {len(unmapped)}", file=sys.stderr)

    # Search OLS for unmapped terms (only short, simple terms)
    ols_cache = {}
    if unmapped:
        print(f"\n=== Searching OLS for {len(unmapped)} unmapped terms ===", file=sys.stderr)
        for i, term in enumerate(sorted(unmapped)):
            # Skip very long/compound terms - OLS gives garbage for these
            if len(term) > 60:
                print(f"  SKIP (too long): {term[:60]}...", file=sys.stderr)
                continue
            # Try GO first
            search_term = term.replace('_', ' ')
            results = ols_search_go(search_term)
            # Only accept if the result label has some word overlap with the query
            match = None
            for oid, label in results:
                query_words = set(search_term.lower().split())
                label_words = set(label.lower().split())
                if query_words & label_words:
                    match = (oid, label)
                    break
            if match:
                ols_cache[term] = match
                print(f"  GO: {term} → {match[0]} {match[1]}", file=sys.stderr)
            else:
                # Try NBO
                results = ols_search_nbo(search_term)
                for oid, label in results:
                    query_words = set(search_term.lower().split())
                    label_words = set(label.lower().split())
                    if query_words & label_words:
                        match = (oid, label)
                        break
                if match:
                    ols_cache[term] = match
                    print(f"  NBO: {term} → {match[0]} {match[1]}", file=sys.stderr)
                else:
                    print(f"  MISS: {term}", file=sys.stderr)
            if (i + 1) % 20 == 0:
                print(f"  Searched {i+1}/{len(unmapped)}", file=sys.stderr)

    # Build final lookup: normalised term → (id, label)
    final_map = dict(FUNCTION_MAP)
    final_map.update(ols_cache)

    # Cell types where song terms refer to song perception, not production
    # (pC1a-e are female neurons responding to male song; Wang et al. 2020)
    # (JO-A are sensory neurons detecting sound, including courtship song)
    SONG_PERCEPTION_TYPES = {'pC1a', 'pC1b', 'pC1c', 'pC1d', 'pC1e', 'JO-A'}
    SONG_TERMS = {'sine_song', 'pulse_song', 'courtship song'}

    # Sex-neutral cell types where egg-laying should not be mapped
    # (these neurons lack female-specific FBbt subclasses)
    EGG_LAYING_SKIP_TYPES = {'DNa12', 'DNg14', 'SMP550'}
    EGG_LAYING_TERMS = {'oviposition', 'egg_laying', 'abdomen_curl', 'vaginal_plate_opening'}

    # Fruitless neuron types without male-specific FBbt subclasses:
    # male-specific song/vibration GO terms must be replaced with courtship behavior
    MALE_SONG_GO = {'GO:0045433', 'GO:0016545'}
    MALE_SONG_REMAP_TYPES = {
        'AN08B031', 'AN08B043', 'AN08B059', 'AN08B069',  # vPR13
        'dMS9', 'dPR1', 'pMP2', 'vMS11', 'vMS13', 'vMS16', 'vPR6',
    }

    # Assemble per-row
    print(f"\n=== Assembling per-row ontology mappings ===", file=sys.stderr)
    for row in rows:
        kf = row['known_function'].strip()
        if not kf:
            row['function_ont_id'] = ''
            row['function_ont_label'] = ''
            continue

        cell_type = row['cell_type'].strip()
        ids = []
        labels = []
        seen = set()
        add_song_perception = False
        for part in split_function_terms(kf):
            norm = normalise_term(part)
            if not norm or norm in SKIP_TERMS:
                continue

            # pC1/JO-A neurons perceive song, not produce it
            if cell_type in SONG_PERCEPTION_TYPES and norm in SONG_TERMS:
                add_song_perception = True
                continue

            # Skip egg-laying terms for sex-neutral anatomy
            if cell_type in EGG_LAYING_SKIP_TYPES and norm in EGG_LAYING_TERMS:
                continue

            mapping = final_map.get(norm)
            if mapping:
                ont_id, ont_label = mapping
                # Replace male-specific song terms with courtship behavior
                # for fruitless neurons lacking male-specific FBbt subclasses
                if cell_type in MALE_SONG_REMAP_TYPES and ont_id in MALE_SONG_GO:
                    ont_id = 'GO:0007619'
                    ont_label = 'courtship behavior'
                if ont_id not in seen:
                    ids.append(ont_id)
                    labels.append(ont_label)
                    seen.add(ont_id)

        if add_song_perception and 'GO:0007605' not in seen:
            ids.append('GO:0007605')
            labels.append('sensory perception of sound')
            seen.add('GO:0007605')

        row['function_ont_id'] = '|'.join(ids)
        row['function_ont_label'] = '|'.join(labels)

    # Write output
    out_fieldnames = list(fieldnames) + ['function_ont_id', 'function_ont_label']
    with open(OUTPUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames, delimiter='\t',
                                extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    # Stats
    has_ont = sum(1 for r in rows if r.get('function_ont_id', '').strip())
    print(f"\nFinal stats:", file=sys.stderr)
    print(f"  Rows with ontology mapping: {has_ont}/{len(rows)}", file=sys.stderr)

    # Unique ontology terms used
    all_ids = set()
    for r in rows:
        for oid in r.get('function_ont_id', '').split('|'):
            if oid.strip():
                all_ids.add(oid.strip())
    print(f"  Unique ontology terms used: {len(all_ids)}", file=sys.stderr)


if __name__ == '__main__':
    main()
