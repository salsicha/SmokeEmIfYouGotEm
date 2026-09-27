[out:json][timeout:120];
(
  relation(12000489);
)->.river;
.river out geom;
(
  node(9.95,-83.60,10.10,-83.44)["whitewater"];
  node(9.95,-83.60,10.10,-83.44)["whitewater:rapid_grade"];
  node(9.95,-83.60,10.10,-83.44)["natural"="rapids"];
  way(9.95,-83.60,10.10,-83.44)["whitewater"];
  way(9.95,-83.60,10.10,-83.44)["waterway"="rapids"];
  node(9.95,-83.60,10.10,-83.44)["waterway"="rapids"];
  way(9.95,-83.60,10.10,-83.44)["natural"="water"]["water"="river"];
  relation(9.95,-83.60,10.10,-83.44)["natural"="water"]["water"="river"];
  way(9.95,-83.60,10.10,-83.44)["waterway"="riverbank"];
);
out geom;
