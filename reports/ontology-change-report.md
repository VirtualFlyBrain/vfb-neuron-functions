# Neuron function ontology — changes from the BANC supplement merge

Comparison of the output ontology **before** the BANC merge (git `a565cad`, `known_types_mapped.tsv`) and **after** (`neuron_functions.tsv` / `vfb-neuron-functions.owl`).

Only cell types that appear in the OWL are considered. A cell type enters the OWL when it has an FBbt term, a function-ontology term, and at least one reference. **The current pipeline additionally excludes non-exact FBbt mappings** (`specificity` = `parent_term` or `general_term`) so functions are only asserted on exact anatomy matches; the pre-BANC pipeline did not. "Source name" is the cell type as written in the source file, with any aliases (`also_known_as` / `other_names`).

## Summary
| Change | Count |
|---|---|
| Cell types added to ontology | 16 |
| Cell types removed from ontology | 23 |
| Changed function pairing | 43 |
| Changed FBbt anatomy term | 9 |

## 1. Added to the ontology

| Source name | Aliases | FBbt ID | FBbt label | Annotation source | Source function text | Function term(s) |
|---|---|---|---|---|---|---|
| AN08B018 *(new)* |  | FBbt:20007872 | adult AN08B018 neuron | BANC | nociception | sensory perception of pain |
| AN09B004 *(new)* |  | FBbt:20007922 | adult AN09B004 neuron | BANC | nociception | sensory perception of pain |
| AN17A026 *(new)* | TwoLumps | FBbt:00049915 | adult TwoLumps ascending neuron | BANC | walking | adult walking behavior |
| AN27X017 *(new)* | bowtie | FBbt:20008099 | adult AN27X017 neuron | BANC | halting | adult walking behavior |
| DNae003 |  | FBbt:20001795 | adult posterior slope neuron 040 | BANC | steering | adult locomotory behavior |
| DNg07 *(new)* |  | FBbt:00047599 | descending neuron of the gnathal ganglion DNg07 | BANC | flight | flight behavior |
| DNg79 *(new)* |  | FBbt:20007517 | descending neuron of the gnathal ganglion DNg79 | BANC | landing | flight behavior |
| DNp05 *(new)* |  | FBbt:00047638 | descending neuron of the posterior brain DNp05 | BANC | escape_takeoff | flight behavior |
| DNp17 *(new)* |  | FBbt:00047650 | descending neuron of the posterior brain DNp17 | BANC | steering | adult locomotory behavior |
| DNp35 *(new)* |  | FBbt:00047668 | descending neuron of the posterior brain DNp35 | BANC | escape_takeoff | flight behavior |
| DNp47 *(new)* |  | FBbt:20002048 | adult posterior slope neuron 293 | BANC | landing | flight behavior |
| DNp60 *(new)* |  | FBbt:20011354 | descending neuron of the posterior brain DNp60 | BANC | threat_response | behavioral defense response |
| DNpe050 *(new)* |  | FBbt:20001046 | adult descending neuron of the posterior brain DNpe050 | BANC | threat_response | behavioral defense response |
| LB1c |  | FBbt:00110887 | gustatory receptor neuron of the labellum | known_types | labellar bristle gustatory receptor neuron; bitter taste | sensory perception of taste, sensory perception of bitter taste |
| LB1e |  | FBbt:00110887 | gustatory receptor neuron of the labellum | known_types | Ir94e labellar bristle gustatory receptor neuron; mild aversive response to glutamate | sensory perception of taste |
| LC13 *(new)* |  | FBbt:00100485 | lobula columnar neuron LC13 | BANC | visual_small_object | visual behavior |

*(new)* = not present in the pre-BANC dataset at all; others were present but previously excluded from the OWL.

## 2. Removed from the ontology

| Source name | Aliases | FBbt ID (was) | FBbt label (was) | Old function term(s) | Why removed |
|---|---|---|---|---|---|
| AN08B031 | vPR13 | FBbt:00053053 | adult fruitless vPR13 neuron | courtship behavior | FBbt mapping is `parent_term` (now excluded) |
| AN08B043 | vPR13 | FBbt:00053053 | adult fruitless vPR13 neuron | courtship behavior | FBbt mapping is `parent_term` (now excluded) |
| AN08B059 | vPR13 | FBbt:00053053 | adult fruitless vPR13 neuron | courtship behavior | FBbt mapping is `parent_term` (now excluded) |
| AN08B069 | vPR13 | FBbt:00053053 | adult fruitless vPR13 neuron | courtship behavior | FBbt mapping is `parent_term` (now excluded) |
| DNc01 | SIFa | FBbt:00047588 | descending neuron of the pars intercerebralis DNc01 | feeding behavior, olfactory behavior | now `neuromodulatory` from BANC (excluded function) |
| DNc02 | SIFa | FBbt:00047589 | descending neuron of the pars intercerebralis DNc02 | reproduction, feeding behavior | now `neuromodulatory` from BANC (excluded function) |
| DNg02 |  | FBbt:00047594 | descending neuron of the gnathal ganglion DNg02 | flight behavior, visual behavior | FBbt mapping is `parent_term` (now excluded) |
| DNg12 |  | FBbt:00047604 | descending neuron of the gnathal ganglion DNg12 | grooming behavior, head movement | FBbt mapping is `parent_term` (now excluded) |
| MN12D |  | FBbt:20004607 | adult CB0914 neuron | feeding behavior | FBbt mapping is `parent_term` (now excluded) |
| MN3L |  | FBbt:20004571 | adult CB0875 neuron | proboscis extension reflex | FBbt mapping is `parent_term` (now excluded) |
| MeTu2a | MeTu-DRA | FBbt:00052133 | adult medulla-tubercle neuron of dorsal rim area | visual perception | FBbt mapping is `parent_term` (now excluded) |
| MeTu2b | MeTu-DRA | FBbt:00052133 | adult medulla-tubercle neuron of dorsal rim area | visual perception | FBbt mapping is `parent_term` (now excluded) |
| MeTu3a |  | FBbt:00053509 | adult medulla-tubercle neuron 3 | visual perception | FBbt mapping is `parent_term` (now excluded) |
| MeTu3b |  | FBbt:00053509 | adult medulla-tubercle neuron 3 | visual perception | FBbt mapping is `parent_term` (now excluded) |
| MeTu3c |  | FBbt:00053509 | adult medulla-tubercle neuron 3 | visual perception | FBbt mapping is `parent_term` (now excluded) |
| TmY9a | TmY9q__perp | FBbt:00003827 | transmedullary Y neuron TmY9 | visual behavior, visual perception | FBbt mapping is `parent_term` (now excluded) |
| TmY9b | TmY9q | FBbt:00003827 | transmedullary Y neuron TmY9 | visual behavior | FBbt mapping is `parent_term` (now excluded) |
| TmY9q | TmY9b | FBbt:00003827 | transmedullary Y neuron TmY9 | visual behavior | FBbt mapping is `parent_term` (now excluded) |
| TmY9q__perp | TmY9a | FBbt:00003827 | transmedullary Y neuron TmY9 | visual behavior | FBbt mapping is `parent_term` (now excluded) |
| lLN2F_b |  | FBbt:00049812 | adult antennal lobe local neuron lLN2F | olfactory behavior | FBbt mapping is `parent_term` (now excluded) |
| lLN2P_a |  | FBbt:00049813 | adult antennal lobe local neuron lLN2P | olfactory behavior | FBbt mapping is `parent_term` (now excluded) |
| lLN2P_b |  | FBbt:00049813 | adult antennal lobe local neuron lLN2P | olfactory behavior | FBbt mapping is `parent_term` (now excluded) |
| lLN2P_c |  | FBbt:00049813 | adult antennal lobe local neuron lLN2P | olfactory behavior | FBbt mapping is `parent_term` (now excluded) |

## 3. Changed function pairing

| Source name | Aliases | FBbt ID | FBbt label | Source | Old function text | Old function term(s) | New function text | New function term(s) |
|---|---|---|---|---|---|---|---|---|
| AN05B102a | PPN1 | FBbt:20007772 | adult AN05B102 neuron | BANC | courtship promotion | courtship behavior | pheromone | response to pheromone |
| DNa01 |  | FBbt:00047572 | descending neuron of the anterior dorsal brain DNa01 | BANC | ipsiversive, low gain steering; turning | flight behavior, turning behavior | steering | adult locomotory behavior |
| DNa02 |  | FBbt:00047573 | descending neuron of the anterior dorsal brain DNa02 | BANC | ipsiversive, high gain steering; shorten stride of the inside leg | flight behavior, adult walking behavior | steering | adult locomotory behavior |
| DNa03 |  | FBbt:00047574 | descending neuron of the anterior dorsal brain DNa03 | BANC | turning; walking | turning behavior, adult walking behavior | steering | adult locomotory behavior |
| DNa11 |  | FBbt:20003474 | adult vest neuron 008 | BANC | rapid saccadic turning; walking | flight behavior, adult walking behavior | steering | adult locomotory behavior |
| DNa15 |  | FBbt:20011334 | descending neuron of the anterior dorsal brain DNa15 | BANC | turning; flight | turning behavior, flight behavior | flight | flight behavior |
| DNb01 |  | FBbt:00047582 | descending neuron of the anterior ventral brain DNb01 | BANC | turning; flight | turning behavior, flight behavior | flight | flight behavior |
| DNb02 |  | FBbt:00047583 | descending neuron of the anterior ventral brain DNb02 | BANC | turning | turning behavior | steering | adult locomotory behavior |
| DNb05 |  | FBbt:00047586 | descending neuron of the anterior ventral brain DNb05 | BANC | ipsiversive steering; turning | flight behavior, turning behavior | steering | adult locomotory behavior |
| DNb06 |  | FBbt:00047587 | descending neuron of the anterior ventral brain DNb06 | BANC | contraversive steering; turning | flight behavior, turning behavior | steering | adult locomotory behavior |
| DNg13 |  | FBbt:00047605 | descending neuron of the gnathal ganglion DNg13 | BANC | ipsiversive steering; turning; lengthen stride of outside leg | flight behavior, turning behavior, adult walking behavior | steering | adult locomotory behavior |
| DNg55 | BDN3 | FBbt:20007500 | descending neuron of the gnathal ganglion DNg55 | BANC | walking | adult walking behavior | steering | adult locomotory behavior |
| DNge172 | mute | FBbt:00051917 | adult mute subesophageal neuron | BANC | oviposition | egg-laying behavior | reproduction | reproduction |
| DNp02 |  | FBbt:00047635 | descending neuron of the posterior brain DNp02 | BANC | backward-jumping; escape_takeoff | backward locomotion, flight behavior | escape_takeoff | flight behavior |
| DNp03 |  | FBbt:00047636 | descending neuron of the posterior brain DNp03 | BANC | flight saccade; respond to looming stimuli | flight behavior, visual behavior | flight | flight behavior |
| DNp06 |  | FBbt:00047639 | descending neuron of the posterior brain DNp06 | BANC | turning, flight; escape_takeoff | turning behavior, flight behavior | escape_takeoff | flight behavior |
| DNp09 | P9 | FBbt:00047642 | descending neuron of the posterior brain DNp09 | BANC | turning on unilateral activation; forward on bilateral activation; abdomen_curl; freezing | turning behavior, adult walking behavior, egg-laying behavior, escape behavior | halting | adult walking behavior |
| DNp11 |  | FBbt:00047644 | descending neuron of the posterior brain DNp11 | BANC | forward-jumping; escape_takeoff | locomotion, flight behavior | escape_takeoff | flight behavior |
| DNp13 | pMN1 | FBbt:00047646 | descending neuron of the posterior brain DNp13 | BANC | oviposition; reproduction | egg-laying behavior, reproduction | reproduction | reproduction |
| DNp15 |  | FBbt:00047648 | descending neuron of the posterior brain DNp15 | BANC | turning, walking, flight | turning behavior, adult walking behavior, flight behavior | steering | adult locomotory behavior |
| DNp20 | DNOVS1 | FBbt:00047653 | descending neuron of the posterior brain DNp20 | BANC | ocellar | visual perception | flight | flight behavior |
| DNp29 | NPFP1 | FBbt:00047662 | descending neuron of the posterior brain DNp29 | BANC | neuromodulatory (dNPF), stimulation mimics food-deprivation; abdomen grooming | feeding behavior, grooming behavior | hunger | feeding behavior |
| DNp37 | vpoDN_pMN2 | FBbt:00048405 | adult vaginal plate opening descending neuron vpoDN | BANC | vaginal_plate_opening | egg-laying behavior | reproduction | reproduction |
| DNp42 |  | FBbt:00052181 | descending neuron of the posterior brain DNp42 | BANC | backing up; geosmin avoidance | backward locomotion, olfactory behavior | walking | adult walking behavior |
| FD1 |  | FBbt:00052268 | lobula plate tangential neuron FD1 | BANC | visual_horizontal_widefieldmotion; visual | visual perception, visual behavior | visual_horizontal_widefieldmotion | visual perception |
| FD3 |  | FBbt:00052269 | lobula plate tangential neuron FD3 | BANC | visual_horizontal_widefieldmotion; visual | visual perception, visual behavior | visual_horizontal_widefieldmotion | visual perception |
| H1 |  | FBbt:00047991 | lobula plate tangential neuron H1 | BANC | visual_horizontal_widefieldmotion; visual | visual perception, visual behavior | visual_horizontal_widefieldmotion | visual perception |
| LC10a |  | FBbt:00111747 | lobula columnar neuron LC10a | BANC | visual_small_object; courtship; visual | visual behavior, courtship behavior | visual_small_object | visual behavior |
| LC12 |  | FBbt:00100484 | lobula columnar neuron LC12 | BANC | visual_loom, visual_large_objects, visual_small_object; visual | visual behavior | visual_object,visual_loom | visual object recognition, visual behavior |
| LC16 |  | FBbt:00111751 | lobula columnar neuron LC16 | BANC | Retreat behavior; visual_loom; backwards, freezing; walking | backward locomotion, visual behavior, escape behavior, adult walking behavior | visual_loom | visual behavior |
| LC17 |  | FBbt:00111752 | lobula columnar neuron LC17 | BANC | visual_loom, visual_large_objects, visual_small_object; electrical synapses for object tracking in flight | visual behavior | visual_object,visual_loom | visual object recognition, visual behavior |
| LC4 |  | FBbt:00003874 | lobula columnar neuron LC4 | BANC | Looming detector; visual_loom; flight; escape_takeoff | visual behavior, flight behavior | visual_loom | visual behavior |
| LC6 |  | FBbt:00003876 | lobula columnar neuron LC6 | BANC | visual_loom, visual_small_object; flight; escape_takeoff | visual behavior, flight behavior | visual_small_object,visual_loom | visual behavior |
| LC9 |  | FBbt:00100480 | lobula columnar neuron LC9 | BANC | visual_loom, visual_small_object; courtship; backward walking | visual behavior, courtship behavior, backward locomotion | visual_small_object,visual_loom | visual behavior |
| LPLC1 |  | FBbt:00111762 | lobula plate-lobula columnar neuron LPLC1 | BANC | visual_loom, collision avoidance | visual behavior, visually guided collision avoidance behavior | visual_loom | visual behavior |
| LPLC2 |  | FBbt:00111763 | lobula plate-lobula columnar neuron LPLC2 | BANC | Looming escape | escape behavior | visual_small_object,visual_loom | visual behavior |
| LT52 |  | FBbt:20011451 | adult lobula tangential neuron LT52 | BANC | detect leg movements during head grooming | grooming behavior | visual_front_leg_feedback | visual behavior |
| MDN | DNp50 | FBbt:00111308 | adult moonwalker descending neuron | BANC | backwards walking | backward locomotion | walking | adult walking behavior |
| MTe50 | ML-VPN1 | FBbt:20007659 | adult medulla visual projection neuron MeVP11 | BANC | visual_chromatic; visual | visual perception, visual behavior | visual_chromatic | visual perception |
| oviDNa | oviDNa | FBbt:00049920 | oviposition descending neuron oviDNa | BANC | oviposition, abdomen_curl | egg-laying behavior | reproduction | reproduction |
| oviDNa_a | oviDNa | FBbt:00049920 | oviposition descending neuron oviDNa | BANC | oviposition, abdomen_curl | egg-laying behavior | reproduction | reproduction |
| oviDNa_b | oviDNb | FBbt:00049920 | oviposition descending neuron oviDNa | BANC | oviposition, abdomen_curl | egg-laying behavior | reproduction | reproduction |
| oviDNb | oviDNb | FBbt:00049921 | oviposition descending neuron oviDNb | BANC | oviposition, abdomen_curl | egg-laying behavior | reproduction | reproduction |

## 4. Changed FBbt anatomy term (function pairing unchanged)

These change the axiom subject in the OWL even though the function pairing is the same. Corrections are recorded in `resources/fbbt_overrides.tsv`.

| Source name | Aliases | Old FBbt ID | Old FBbt label | New FBbt ID | New FBbt label | Function term(s) | Reason |
|---|---|---|---|---|---|---|---|
| CB0339 | LHPD2b1 | FBbt:00049371 | adult lateral horn PD2b1 neuron | FBbt:00049369 | adult lateral horn PD2a2 neuron | memory, olfactory behavior | corrected from PD2b1 (FBbt:00049371) per all_male-cns_FBbt.tsv |
| DNa04 |  | FBbt:20008279 | adult DNut060 neuron | FBbt:00047575 | descending neuron of the anterior dorsal brain DNa04 | flight behavior | corrected from DNut060 (FBbt:20008279) per male-cns 'type' column |
| DNa05 |  | FBbt:20008259 | adult DNut037 neuron | FBbt:00047576 | descending neuron of the anterior dorsal brain DNa05 | flight behavior | corrected from DNut037 (FBbt:20008259) per male-cns 'type' column |
| DNb01 |  | FBbt:00053057 | descending neuron of the anterior ventral brain DNb09 | FBbt:00047582 | descending neuron of the anterior ventral brain DNb01 | flight behavior | corrected from DNb09 (FBbt:00053057) per male-cns 'type' column |
| DNb06 |  | FBbt:20008249 | adult DNnt015 neuron | FBbt:00047587 | descending neuron of the anterior ventral brain DNb06 | adult locomotory behavior | corrected from DNnt015 (FBbt:20008249) per male-cns 'type' column |
| DNp09 | P9 | FBbt:20011344 | descending neuron of the posterior brain DNp71 | FBbt:00047642 | descending neuron of the posterior brain DNp09 | adult walking behavior | corrected from DNp71 (FBbt:20011344); DNp71 lists DNp09 as its hemibrainType, causing a name-match error in the original curation |
| R7d |  | FBbt:00004225 | photoreceptor cell R7 | FBbt:00004449 | dorsal margin photoreceptor cell R7 | detection of UV | was generic R7 (FBbt:00004225) |
| R7p |  | FBbt:00004225 | photoreceptor cell R7 | FBbt:02000006 | photoreceptor cell R7 of pale ommatidium | detection of UV | was generic R7 (FBbt:00004225) |
| R8d |  | FBbt:00004227 | photoreceptor cell R8 | FBbt:00004209 | dorsal margin photoreceptor cell R8 | detection of UV | was generic R8 (FBbt:00004227) |

