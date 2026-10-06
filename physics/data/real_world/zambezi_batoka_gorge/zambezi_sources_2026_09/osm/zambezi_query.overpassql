[out:json][timeout:180][bbox:-18.10,25.75,-17.85,26.10];
(
  way["waterway"="river"];
  node["whitewater"];
  node["waterway"~"rapids|waterfall"];
  way["waterway"="rapids"];
  node["name"~"Rapid|Boiling Pot|Mukuni|Batoka",i];
  way["natural"="water"]["water"="river"];
);
out body;
>;
out skel qt;
