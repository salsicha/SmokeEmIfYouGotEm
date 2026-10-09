[out:json][timeout:120];
(
  relation(12000489);
)->.river;
.river out geom;
(
  node(9.9380,-83.5616,10.1077,-83.4741)["whitewater"];
  node(9.9380,-83.5616,10.1077,-83.4741)["whitewater:rapid_grade"];
  node(9.9380,-83.5616,10.1077,-83.4741)["natural"="rapids"];
  way(9.9380,-83.5616,10.1077,-83.4741)["whitewater"];
  way(9.9380,-83.5616,10.1077,-83.4741)["waterway"="rapids"];
  node(9.9380,-83.5616,10.1077,-83.4741)["waterway"="rapids"];
  way(9.9380,-83.5616,10.1077,-83.4741)["natural"="water"]["water"="river"];
  relation(9.9380,-83.5616,10.1077,-83.4741)["natural"="water"]["water"="river"];
  way(9.9380,-83.5616,10.1077,-83.4741)["waterway"="riverbank"];
);
out geom;
