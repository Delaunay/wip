"""
    This the definition of board of the standard diplomacy 1971 Game of 1901 Europe.

    The dgame engine will only manipulate numbers and no reference to the actual name should be made.
    You can use `Powers` and `Provinces` to access the different struct

    To make the dgame engine able to process custom diplomacy boards one needs to implement
    the current module.
"""

from enum import auto, IntEnum, unique
from dgame.province import Province
from dgame.definition import BoardDefinition


def make_adjacency_list(SUPPLY_CENTERS, WATER_TILES, adjacency_map, Provinces, HOME_SUPPLY_CENTERS):
    """
        Make a tuple from an adjacency map,
        since our provinces are numbers we can just do index lookup and not use a map at all.
        Because the map never changes we no dot use an array but a tuple so modification is not allowed
    """

    return tuple(Province(
        pid=item,
        supply_center=item in SUPPLY_CENTERS,
        water=item in WATER_TILES,
        home_center=item in HOME_SUPPLY_CENTERS,
        coastal=[item for item in adjacency_map[item.value] if item in WATER_TILES],
        neighbours=adjacency_map[item.value]) for item in list(Provinces))


class Diplomacy1901(BoardDefinition):
    @unique
    class Powers(IntEnum):
        AustriaHungary = auto()
        England = auto()
        France = auto()
        Germany = auto()
        Italy = auto()
        Russia = auto()
        Turkey = auto()

    @unique
    class Provinces(IntEnum):
        SWI = 0       # Switzerland,
        ADR = auto()  # Adriatic Sea,
        AEG = auto()  # Aegean Sea,
        ALB = auto()  # Albania,
        ANK = auto()  # Ankara,
        APU = auto()  # Apulia,
        ARM = auto()  # Armenia,
        BAL = auto()  # Baltic Sea,
        BAR = auto()  # Barents Sea,
        BEL = auto()  # Belgium,
        BER = auto()  # Berlin,
        BLA = auto()  # Black Sea,
        BOH = auto()  # Bohemia,
        BRE = auto()  # Brest,
        BUD = auto()  # Budapest,
        BUL = auto()  # Bulgaria,
        BUR = auto()  # Burgundy,
        CLY = auto()  # Clyde,
        CON = auto()  # Constantinople,
        DEN = auto()  # Denmark,
        EAS = auto()  # Eastern Mediterranean,
        EDI = auto()  # Edinburgh,
        ENG = auto()  # English Channel,
        FIN = auto()  # Finland,
        GAL = auto()  # Galicia,
        GAS = auto()  # Gascony,
        GRE = auto()  # Greece,
        LYO = auto()  # Gulf of Lyon,
        BOT = auto()  # Gulf of Bothnia,
        HEL = auto()  # Helgoland Bight,
        HOL = auto()  # Holland,
        ION = auto()  # Ionian Sea,
        IRI = auto()  # Irish Sea,
        KIE = auto()  # Kiel,
        LVP = auto()  # Liverpool,
        LVN = auto()  # Livonia,
        LON = auto()  # London,
        MAR = auto()  # Marseilles,
        MAO = auto()  # Mid-Atlantic Ocean,
        MOS = auto()  # Moscow,
        MUN = auto()  # Munich,
        NAP = auto()  # Naples,
        NAO = auto()  # North Atlantic Ocean,
        NAF = auto()  # North Africa,
        NTH = auto()  # North Sea,
        NOR = auto()  # Norway,
        NWG = auto()  # Norwegian Sea,
        PAR = auto()  # Paris,
        PIC = auto()  # Picardy,
        PIE = auto()  # Piedmont,
        POR = auto()  # Portugal,
        PRU = auto()  # Prussia,
        ROM = auto()  # Rome,
        RUH = auto()  # Ruhr,
        RUM = auto()  # Rumania,
        SER = auto()  # Serbia,
        SEV = auto()  # Sevastopol,
        SIL = auto()  # Silesia,
        SKA = auto()  # Skagerrak,
        SMY = auto()  # Smyrna,
        SPA = auto()  # Spain,
        STP = auto()  # St Petersburg,
        SWE = auto()  # Sweden,
        SYR = auto()  # Syria,
        TRI = auto()  # Trieste,
        TUN = auto()  # Tunis,
        TUS = auto()  # Tuscany,
        TYR = auto()  # Tyrolia,
        TYS = auto()  # Tyrrhenian Sea,
        UKR = auto()  # Ukraine,
        VEN = auto()  # Venice,
        VIE = auto()  # Vienna,
        WAL = auto()  # Wales,
        WAR = auto()  # Warsaw,
        WES = auto()  # Western Mediterranean,
        YOR = auto()  # Yorkshire,

        def __repr__(self):
            return self.name

    SWI = Provinces.SWI
    ADR = Provinces.ADR
    AEG = Provinces.AEG
    ALB = Provinces.ALB
    ANK = Provinces.ANK
    APU = Provinces.APU
    ARM = Provinces.ARM
    BAL = Provinces.BAL
    BAR = Provinces.BAR
    BEL = Provinces.BEL
    BER = Provinces.BER
    BLA = Provinces.BLA
    BOH = Provinces.BOH
    BRE = Provinces.BRE
    BUD = Provinces.BUD
    BUL = Provinces.BUL
    BUR = Provinces.BUR
    CLY = Provinces.CLY
    CON = Provinces.CON
    DEN = Provinces.DEN
    EAS = Provinces.EAS
    EDI = Provinces.EDI
    ENG = Provinces.ENG
    FIN = Provinces.FIN
    GAL = Provinces.GAL
    GAS = Provinces.GAS
    GRE = Provinces.GRE
    LYO = Provinces.LYO
    BOT = Provinces.BOT
    HEL = Provinces.HEL
    HOL = Provinces.HOL
    ION = Provinces.ION
    IRI = Provinces.IRI
    KIE = Provinces.KIE
    LVP = Provinces.LVP
    LVN = Provinces.LVN
    LON = Provinces.LON
    MAR = Provinces.MAR
    MAO = Provinces.MAO
    MOS = Provinces.MOS
    MUN = Provinces.MUN
    NAP = Provinces.NAP
    NAO = Provinces.NAO
    NAF = Provinces.NAF
    NTH = Provinces.NTH
    NOR = Provinces.NOR
    NWG = Provinces.NWG
    PAR = Provinces.PAR
    PIC = Provinces.PIC
    PIE = Provinces.PIE
    POR = Provinces.POR
    PRU = Provinces.PRU
    ROM = Provinces.ROM
    RUH = Provinces.RUH
    RUM = Provinces.RUM
    SER = Provinces.SER
    SEV = Provinces.SEV
    SIL = Provinces.SIL
    SKA = Provinces.SKA
    SMY = Provinces.SMY
    SPA = Provinces.SPA
    STP = Provinces.STP
    SWE = Provinces.SWE
    SYR = Provinces.SYR
    TRI = Provinces.TRI
    TUN = Provinces.TUN
    TUS = Provinces.TUS
    TYR = Provinces.TYR
    TYS = Provinces.TYS
    UKR = Provinces.UKR
    VEN = Provinces.VEN
    VIE = Provinces.VIE
    WAL = Provinces.WAL
    WAR = Provinces.WAR
    WES = Provinces.WES
    YOR = Provinces.YOR

    POWERS_HOME_SUPPLY_CENTERS = (
        (BUD, TRI, VIE),  # AustriaHungary
        (EDI, LVP, LON),  # England
        (BRE, MAR, PAR),  # France
        (BER, KIE, MUN),  # Germany
        (NAP, ROM, VEN),  # Italy
        (MOS, SEV, STP, WAR),  # Russia
        (ANK, CON, SMY),  # Turkey
    )

    WATER_TILES = frozenset(
            {ADR, AEG, BAL, BAR, BLA, EAS, ENG, LYO, BOT, HEL, ION, IRI, MAO, NAO, NTH, NWG, SKA, TYS, WES})

    LAND_TILES = frozenset(set(Provinces.__members__.values()).difference(WATER_TILES))

    HOME_SUPPLY_CENTERS = frozenset([x for item in POWERS_HOME_SUPPLY_CENTERS for x in item])

    NEUTRAL_SUPPLY_CENTERS = frozenset({
        BEL, BUL, DEN, GRE, HOL, NOR, POR, RUM, SER, SPA, SWE, TUN
    })

    SUPPLY_CENTERS = frozenset(
        [item for item in NEUTRAL_SUPPLY_CENTERS] + list(HOME_SUPPLY_CENTERS)
    )

    adjacency_map = {
        SWI: (),
        CLY: (EDI, LVP, NWG, NAO),
        EDI: (CLY, YOR, NWG, NTH),
        LVP: (CLY, WAL, NAO, IRI),
        YOR: (EDI, NTH, LON),
        WAL: (LVP, IRI, LON, ENG),
        LON: (YOR, WAL, NTH, ENG),
        NAF: (TUN, MAO, WES),
        TUN: (WES, TYS, ION, NAF),
        NAP: (ROM, APU, TYS, ION),
        ROM: (NAP, TUS, TYS),
        TUS: (ROM, PIE, LYO, TYS),
        PIE: (TUS, MAR, LYO),
        VEN: (APU, ADR, TRI),
        APU: (NAP, VEN, ION, ADR),
        ALB: (GRE, ION, ADR, TRI),
        SER: (GRE, ALB, BUL, RUM, TRI, BUD),
        RUM: (SEV, BLA, BUL),
        CON: (SMY, ANK, AEG, BLA, BUL, BUL),
        SMY: (CON, SYR, AEG, EAS),
        ANK: (CON, ARM, BLA),
        ARM: (ANK, SEV, BLA),
        SYR: (SMY, EAS),
        SEV: (RUM, ARM, BLA),
        UKR: (RUM, SEV, WAR, MOS, GAL),
        WAR: (UKR, LVN, MOS, PRU, SIL, GAL),
        LVN: (PRU, BAL, BOT, STP),
        MOS: (SEV, UKR, WAR, LVN, STP),
        FIN: (SWE, BOT, STP),
        SWE: (FIN, NOR, DEN, SKA, BAL, BOT),
        NOR: (SWE, BAR, NWG, NTH, SKA, STP),
        DEN: (SWE, KIE, NTH, SKA, HEL, BAL),
        KIE: (DEN, BER, HOL, HEL, BAL),
        BER: (KIE, PRU, BAL, SIL),
        PRU: (LVN, BER, BAL),
        SIL: (WAR, BER, PRU, MUN, BOH, GAL),
        MUN: (KIE, BER, SIL, RUH, BUR, TYR, BOH),
        RUH: (KIE, MUN, HOL, BEL, BUR),
        HOL: (KIE, BEL, NTH, HEL),
        BEL: (HOL, PIC, NTH, ENG),
        PIC: (BEL, BRE, ENG),
        BRE: (PIC, GAS, ENG, MAO),
        PAR: (PIC, BRE, BUR, GAS),
        BUR: (MUN, RUH, BEL, PIC, PAR, MAR, GAS),
        MAR: (PIE, LYO, SPA),
        GAS: (BRE, MAO, SPA),
        TYR: (PIE, VEN, MUN, BOH, VIE, TRI),
        BOH: (SIL, MUN, TYR, VIE, GAL),
        VIE: (TYR, BOH, TRI, BUD, GAL),
        TRI: (VEN, ALB, ADR),
        BUD: (SER, RUM, VIE, TRI, GAL),
        GAL: (RUM, UKR, WAR, SIL, BOH, VIE, BUD),
        BUL: (GRE, SER, RUM, CON),
        SPA: (MAR, GAS, POR),
        POR: (MAO, SPA, SPA),
        GRE: (ALB, ION, AEG, BUL),
        STP: (LVN, MOS, FIN, NOR),

        # Water Tiles
        ADR: (VEN, APU, ALB, ION, TRI),
        AEG: (GRE, CON, SMY, ION, EAS, BUL),
        BAL: (LVN, SWE, DEN, KIE, BER, PRU, BOT),
        BAR: (NOR, NWG, STP),
        BLA: (RUM, CON, ANK, ARM, SEV, BUL),
        EAS: (SMY, SYR, ION, AEG),
        ENG: (BEL, PIC, BRE, WAL, NTH, IRI, LON, MAO),
        LYO: (TUS, PIE, MAR, WES, TYS, SPA),
        BOT: (LVN, FIN, SWE, BAL, STP),
        HEL: (DEN, KIE, HOL, NTH),
        ION: (TUN, NAP, APU, GRE, ALB, TYS, ADR, AEG, EAS),
        IRI: (LVP, WAL, NAO, ENG, MAO),
        MAO: (BRE, GAS, NAO, IRI, ENG, WES, POR, SPA, SPA, NAF),
        NAO: (CLY, LVP, NWG, IRI, MAO),
        NTH: (EDI, NOR, DEN, YOR, HOL, BEL, NWG, SKA, HEL, LON, ENG),
        NWG: (CLY, EDI, NOR, BAR, NTH, NAO),
        SKA: (SWE, NOR, DEN, NTH),
        TYS: (TUN, NAP, ROM, TUS, WES, LYO, ION),
        WES: (TUN, MAO, LYO, TYS, SPA, NAF),
    }

    PROVINCE_DB = make_adjacency_list(SUPPLY_CENTERS, WATER_TILES, adjacency_map, Provinces, HOME_SUPPLY_CENTERS)

    def province_from_string(self, name: str) -> Provinces:
        return self.PROVINCE_DB[self.Provinces[name]]

    assert len(PROVINCE_DB) == 76
    assert len(NEUTRAL_SUPPLY_CENTERS) == 12
    assert len(SUPPLY_CENTERS) == 34
    assert len(LAND_TILES) == (76 - 19)
    assert len(WATER_TILES) == 19

    water_list = {
        'SPA/NC': ('GAS', 'MAO', 'POR'),
        'SPA/SC': ('MAR', 'MAO', 'WES', 'LYO', 'POR'),
        'STP/NC': ('NOR', 'BAR'),
        'STP/SC': ('LVN', 'FIN', 'BOT'),
        'BUL/EC': ('RUM', 'CON', 'BLA'),
        'BUL/SC': ('GRE', 'CON', 'AEG')
    }


if __name__ == '__main__':

    boarddef = Diplomacy1901()

    print(boarddef.PROVINCE_DB)
    print(boarddef.LAND_TILES)
    print(boarddef.SUPPLY_CENTERS)

    print(boarddef.province_from_string('GAS'))

