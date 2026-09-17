"""Decorative page themes. No server configuration, network, or filesystem access."""
from dataclasses import dataclass


@dataclass(frozen=True)
class WorldTheme:
    key: str
    page: str
    expansion: str
    title: str
    subtitle: str
    accent: str
    sky: str
    glow: str


THEMES = (
    WorldTheme("home", "Home", "The Burning Crusade", "Your next adventure begins here.",
               "A familiar world. A hearth of your own.", "#d6e99a", "#18243c", "#69d990"),
    WorldTheme("characters", "Characters", "Legion", "The people of your realm",
               "Every adventurer has a story worth keeping.", "#c9b9f5", "#261c46", "#ad84ed"),
    WorldTheme("archives", "Archives", "Mists of Pandaria", "Your adventures, kept close",
               "A quiet library for the journeys behind you.", "#9fdfc7", "#133b3e", "#79cda7"),
    WorldTheme("backups", "Backups", "Wrath of the Lich King", "A vault for your world",
               "Keep a safe copy before the next expedition.", "#b5ddfa", "#172d49", "#71beec"),
    WorldTheme("sources", "Sources", "Warlords of Draenor", "Provision the expedition",
               "Discover, preserve, and understand your sources.", "#f0c795", "#42332f", "#e3ad6b"),
    WorldTheme("workshop", "Workshop", "Cataclysm", "A world waiting to be shaped",
               "The future workshop. Ideas first; creation tools still to come.", "#ffc39b", "#3a202c", "#f28554"),
)
THEMES_BY_KEY = {theme.key: theme for theme in THEMES}
REALM_NOTICE = "Managed realm: Wrath 3.3.5a / build 12340. Page artwork is decorative; it does not switch realms."

# Original, deliberately stylized vector scenes. No external assets or Blizzard files.
SCENES = {
    "home": '''<path d="M470 282L610 125 688 250 775 130 903 271 1060 159 1200 287V360H470Z" fill="#263747"/>
<path d="M560 314L720 232 785 268 901 202 1115 301 1200 279V360H560Z" fill="#172d33"/>
<path d="M746 360L834 273H947L1070 360" fill="#3c4c43"/>
<path d="M821 284V124Q885 24 949 124V284Z" fill="#142728" stroke="#a7bb78" stroke-width="18"/>
<path d="M840 281V132Q885 62 930 132V281Z" fill="url(#light)"/>
<path d="M815 296V117L794 82 823 88 837 112M955 296V117L976 82 947 88 934 112" fill="none" stroke="#56645a" stroke-width="17"/>
<path d="M850 256Q904 220 866 180T908 127M860 274Q930 216 902 158" fill="none" stroke="#c5faba" stroke-width="3" opacity=".6"/>
<g fill="#ccdf94"><path d="M817 151l7-9 7 9-7 9ZM817 192l7-9 7 9-7 9ZM817 233l7-9 7 9-7 9ZM939 151l7-9 7 9-7 9ZM939 192l7-9 7 9-7 9ZM939 233l7-9 7 9-7 9Z"/></g>
<path d="M1050 308l18-100 21 100M1100 309l21-147 23 147" fill="#365646"/>
<ellipse cx="891" cy="303" rx="130" ry="12" fill="#93d995" opacity=".12"/>''',
    "characters": '''<circle cx="910" cy="156" r="114" fill="#362b58" stroke="#75658e" stroke-width="3"/>
<circle cx="910" cy="156" r="88" fill="#24223e" stroke="#b995d6" stroke-width="2"/>
<path d="M910 61V250M817 156H1003M844 90L977 223M844 222L977 89" stroke="#70618e" stroke-width="2"/>
<path d="M710 304V76L733 50 756 76V304M1060 304V76L1083 50 1106 76V304" fill="#34334e" stroke="#60586e" stroke-width="5"/>
<path d="M771 73H820V190L795 212 771 190ZM1001 73H1050V190L1025 212 1001 190Z" fill="#64518a" stroke="#ba91c5" stroke-width="2"/>
<path d="M791 100l5-12 5 12 12 5-12 5-5 12-5-12-12-5ZM1021 100l5-12 5 12 12 5-12 5-5 12-5-12-12-5Z" fill="#dcc5ec"/>
<path d="M908 84l-13 114 15 17 15-17-13-114Z" fill="#d9ecdb" stroke="#91c2ad" stroke-width="2"/>
<path d="M877 208l33-11 33 11-7 10-26-7-26 7Z" fill="#b7a276"/>
<path d="M905 214h10v31h-10Z" fill="#c3a2d9"/>
<circle cx="910" cy="251" r="7" fill="#ded3a9"/>
<path d="M797 313l32-33h162l35 33ZM766 337l28-21h235l29 21Z" fill="#535069" stroke="#89819b" stroke-width="2"/>
<path d="M679 360l61-41h348l56 41Z" fill="#24243a"/>''',
    "archives": '''<circle cx="1013" cy="94" r="39" fill="#d5e7bf" opacity=".85"/>
<path d="M520 259L647 131 687 212 780 97 831 196 875 145 994 280V360H520Z" fill="#427575" opacity=".65"/>
<path d="M648 277L749 183 781 254 930 178 1037 274 1139 180 1200 257V360H648Z" fill="#295858"/>
<path d="M450 290Q790 259 1200 288V360H450Z" fill="#255052"/>
<path d="M687 305h443M784 326h243M925 343h215" stroke="#88c3ad" opacity=".35" stroke-width="3"/>
<path d="M877 284V180h178v104" fill="#735440" stroke="#b39e69" stroke-width="4"/>
<path d="M852 182Q910 170 966 122 1023 171 1080 182L1051 196H877Z" fill="#285d50" stroke="#a3b875" stroke-width="4"/>
<path d="M890 148Q930 140 966 107 1003 140 1042 148L1024 158H907Z" fill="#347a60" stroke="#accb83" stroke-width="3"/>
<path d="M910 282V211h113v71M946 211v71M985 211v71" fill="#d9bd78" stroke="#755542" stroke-width="6"/>
<path d="M836 288h260l17 15H814Z" fill="#537b6b"/>
<path d="M1116 360Q1091 222 1127 93M1120 360Q1141 256 1156 140" fill="none" stroke="#293f37" stroke-width="8"/>
<path d="M1120 168q-65-32-52-55 48 7 52 55M1121 173q69-33 75-13-15 38-75 13M1143 221q-50-52-62-26 16 40 62 26" fill="#497657"/>
<path d="M568 302q51-65 111 0" fill="none" stroke="#b19463" stroke-width="9"/>''',
    "backups": '''<path d="M516 297L628 83 693 213 768 101 841 252 948 104 1033 238 1121 74 1200 269V360H516Z" fill="#416780"/>
<path d="M580 290L628 83 653 195 626 176 609 221ZM1080 220L1121 74 1148 185 1119 158Z" fill="#9bc3d4"/>
<path d="M756 313V120l39-48h234l39 48v193Z" fill="#304357" stroke="#7e9baf" stroke-width="7"/>
<path d="M810 313V158a102 102 0 0 1 204 0v155Z" fill="#172c45" stroke="#5e8aa8" stroke-width="12"/>
<circle cx="912" cy="205" r="72" fill="#203b54" stroke="#83c5e4" stroke-width="4"/>
<circle cx="912" cy="205" r="53" fill="url(#light)"/>
<path d="M912 125V285M832 205H992M855 148L969 262M855 262L969 148" stroke="#a2e6f7" stroke-width="2"/>
<path d="M912 169l24 36-24 36-24-36Z" fill="#daeef3"/>
<g stroke="#a6dcee" stroke-width="3" fill="none"><path d="M780 168l8-14 8 14-8 14ZM780 226l8-14 8 14-8 14ZM1028 168l8-14 8 14-8 14ZM1028 226l8-14 8 14-8 14Z"/></g>
<path d="M774 85l9 55 9-55M809 77l10 34 10-34M982 77l10 49 10-49M1020 85l10 57 10-57" fill="#b3dfec"/>
<path d="M713 345l36-30h326l43 30Z" fill="#7b9eb3"/>
<path d="M650 360l50-20h431l69 20" fill="#b6d3de"/>''',
    "sources": '''<path d="M440 283L638 150 756 240 898 133 1011 226 1120 142 1200 254V360H440Z" fill="#665047"/>
<path d="M621 323L755 204 846 298 1000 226 1200 305V360H621Z" fill="#3e3936"/>
<path d="M842 296L964 145 1081 296Z" fill="#ad7950" stroke="#e4b879" stroke-width="4"/>
<path d="M942 296l22-151 37 151Z" fill="#463c37"/>
<path d="M797 315l46-17 235 0 44 17" fill="none" stroke="#b09065" stroke-width="3"/>
<path d="M746 282V92M746 102h80l-18 37 18 33h-80Z" fill="#8a4840" stroke="#bb8a61" stroke-width="4"/>
<path d="M774 113l18 14-18 27-15-27Z" fill="#ddbc7d"/>
<path d="M605 299h132v47H605Z" fill="#79583e" stroke="#c49d69" stroke-width="4"/>
<path d="M611 306h120M615 315h17v22h-17M704 315h17v22h-17" stroke="#403b36" stroke-width="5"/>
<path d="M1044 252h90v76h-90Z" fill="#725239" stroke="#b59364" stroke-width="4"/>
<path d="M1049 256l80 68M1129 256l-80 68" stroke="#bb9260" stroke-width="5"/>
<path d="M770 309l24-36 26 36-26 10Z" fill="#e2ac64"/>
<path d="M785 310l10-24 12 24Z" fill="#ffe0a1"/>
<path d="M715 351l56-20 88 16 63-17 66 19" fill="none" stroke="#b7a17d" stroke-width="2"/>
<circle cx="1108" cy="89" r="32" fill="#ddac6c" opacity=".55"/>''',
    "workshop": '''<path d="M463 285L615 127 717 248 861 72 980 245 1094 128 1200 281V360H463Z" fill="#4e3540"/>
<path d="M777 181L861 72 921 161l-52-19-32 20Z" fill="#a04c3f"/>
<path d="M855 147l-18 55 30 42-57 55 19 61h100l-49-67 34-52-40-42 5-57Z" fill="#ec7745"/>
<path d="M862 154l-9 50 33 38-52 57 25 61" fill="none" stroke="#ffc56b" stroke-width="9"/>
<path d="M671 323V199h70v-31h35v155M1044 323V196h39v-25h47v152" fill="#352c35" stroke="#76605c" stroke-width="5"/>
<path d="M744 292h193l-36 37H786Z" fill="#59616a" stroke="#b3a7a2" stroke-width="4"/>
<path d="M819 329h58v18h-58ZM793 348h111v12H793Z" fill="#65616b" stroke="#ba9883" stroke-width="3"/>
<path d="M795 223l53-29 25 46-53 28Z" fill="#81818c" stroke="#d4a68b" stroke-width="3"/>
<path d="M845 247l42 52" stroke="#b78259" stroke-width="12"/>
<path d="M909 280l23-39M924 292l42-16M900 267l1-27" stroke="#ffd18c" stroke-width="3"/>
<path d="M970 344q78-41 167 0" fill="none" stroke="#f28a49" stroke-width="6"/>
<path d="M612 360l50-29h122l-27 29M950 360l25-32h179l46 32" fill="#2f2831"/>''',
}


def scenic_svg(key: str) -> str:
    """Return a self-contained 1200x360 scene, with a dark text-safe left side."""
    theme = THEMES_BY_KEY[key]
    stars = "".join(
        f'<circle cx="{540 + (i * 73) % 640}" cy="{22 + (i * 47) % 200}" '
        f'r="{1 + i % 2}" fill="{theme.accent}" opacity=".35"/>'
        for i in range(28)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360">
<defs>
<linearGradient id="sky" x2="0" y2="1"><stop stop-color="{theme.sky}"/><stop offset="1" stop-color="#111e25"/></linearGradient>
<radialGradient id="light"><stop stop-color="{theme.accent}"/><stop offset=".42" stop-color="{theme.glow}"/><stop offset="1" stop-color="{theme.sky}"/></radialGradient>
<linearGradient id="shade"><stop stop-color="#101920"/><stop offset=".43" stop-color="#101920" stop-opacity=".98"/><stop offset=".64" stop-color="#101920" stop-opacity=".18"/><stop offset="1" stop-color="#101920" stop-opacity="0"/></linearGradient>
</defs>
<rect width="1200" height="360" fill="url(#sky)"/>
<ellipse cx="905" cy="170" rx="272" ry="162" fill="url(#light)" opacity=".2"/>
{stars}{SCENES[key]}
<rect width="1200" height="360" fill="url(#shade)"/>
<rect x="7" y="7" width="1186" height="346" rx="3" fill="none" stroke="{theme.accent}" opacity=".55"/>
<rect x="13" y="13" width="1174" height="334" rx="2" fill="none" stroke="{theme.accent}" opacity=".18"/>
<path d="M18 41V18h23M1159 18h23v23M18 319v23h23M1159 342h23v-23" fill="none" stroke="{theme.accent}" stroke-width="3"/>
<path d="M29 25l5 5-5 5-5-5ZM1171 25l5 5-5 5-5-5ZM29 325l5 5-5 5-5-5ZM1171 325l5 5-5 5-5-5Z" fill="{theme.accent}"/>
</svg>'''
