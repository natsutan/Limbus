PROGRAM RoutinesTest(input, output);

CONST
    five = 5;
TYPE
    enum = (alpha, beta, gamma);
    arr = ARRAY [1..five] OF real;

VAR
    e, k : enum;
    i, m : integer;
    a : arr;
    v, y : real;
    t : boolean;

FUNCTION forwarded(m : integer; VAR t : real) : real; forward;


BEGIN {RoutinesTest}
    e := beta;
END {RoutinesTest}.
