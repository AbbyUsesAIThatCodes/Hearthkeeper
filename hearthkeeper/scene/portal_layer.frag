// WoW's additive effect layers need a separate material after glTF import.
// The texture and geometry are original; the rendering adapter is Hearthkeeper's.
VARYING vec2 portalUV;
void MAIN() {
    vec4 sampleColor = texture(colorMap, portalUV + vec2(uShift, 0.0));
    FRAGCOLOR = vec4(sampleColor.rgb * uGain, sampleColor.a);
}
