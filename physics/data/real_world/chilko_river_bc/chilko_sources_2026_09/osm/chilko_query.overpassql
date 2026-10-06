[out:json][timeout:180];
(
  relation["waterway"="river"]["name"~"Chilko|Taseko"](51.60,-124.20,52.10,-123.55);
  way["waterway"~"river|stream"]["name"~"Chilko|Taseko|Bidwell"](51.60,-124.20,52.10,-123.55);
  node["whitewater"](51.60,-124.20,52.10,-123.55);
  node["waterway"="rapids"](51.60,-124.20,52.10,-123.55);
  way["waterway"="rapids"](51.60,-124.20,52.10,-123.55);
  node["name"~"Bidwell|White Mile|Eagle|Landslide|Lava Canyon",i](51.60,-124.20,52.10,-123.55);
  way["name"~"Lava Canyon",i](51.60,-124.20,52.10,-123.55);
  way["natural"="water"]["water"="river"](51.60,-124.20,52.10,-123.55);
);
out body;
>;
out skel qt;
