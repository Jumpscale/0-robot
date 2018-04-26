@0xdeefaf6aba1a824f;

struct Schema{
    ip @0 :Text;
    port @1 :Int16;

    list @2 :List(Int16);

    sub @3 :Sub;

    struct Sub {
        foo @0 :Text;
    }
}