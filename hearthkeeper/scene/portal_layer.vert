VARYING vec2 portalUV;
void MAIN() {
    portalUV = UV0;
    POSITION = MODELVIEWPROJECTION_MATRIX * vec4(VERTEX, 1.0);
}
