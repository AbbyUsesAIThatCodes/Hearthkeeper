import QtQuick
import QtQuick3D

View3D {
    id: view
    objectName: "portalView"
    property url studySource
    property bool sceneActive: false
    property int cameraIndex: 0
    property real sceneSeconds: 0
    property int frameCount: 0
    property bool modelReady: portal.status === Loader3D.Ready
    property vector3d actionScreen: {
        width; height; cameraIndex;
        if (!camera) return Qt.vector3d(width / 2, height / 2, 0);
        return mapFrom3DScene(Qt.vector3d(0.6, 2.7, 0));
    }
    signal assetError(string detail)

    // Fixed camera: animation belongs to the Portal, not to the reader's viewpoint.
    NumberAnimation on sceneSeconds {
        from: 0; to: 3333 * 6667 / 1000
        duration: 3333 * 6667
        loops: Animation.Infinite
        running: true
        paused: !view.sceneActive
    }
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#10151a"
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: SceneEnvironment.Medium
        tonemapMode: SceneEnvironment.TonemapModeLinear
    }
    PerspectiveCamera {
        id: approach
        // Original model is about 10 units high and faces positive X.
        position: Qt.vector3d(17.0, 4.6, 0)
        eulerRotation: Qt.vector3d(1.0, 90, 0)
        fieldOfView: 46
        fieldOfViewOrientation: PerspectiveCamera.Vertical
        clipNear: 0.05; clipFar: 200
    }
    PerspectiveCamera {
        id: overlook
        position: Qt.vector3d(14.8, 11.8, 4.8)
        eulerRotation: Qt.vector3d(-25, 72, 0)
        fieldOfView: 46
        fieldOfViewOrientation: PerspectiveCamera.Vertical
        clipNear: 0.05; clipFar: 200
    }
    camera: cameraIndex === 0 ? approach : overlook
    DirectionalLight {
        eulerRotation: Qt.vector3d(-35, -45, 0)
        color: "#e7d3bc"
        ambientColor: "#808b99"
        brightness: 0.95
    }
    PointLight {
        position: Qt.vector3d(2.4, 3.1, 0)
        color: "#9aff61"
        brightness: 0.5
        quadraticFade: 0.2
    }
    Loader3D {
        id: portal
        source: view.studySource
        onStatusChanged: {
            if (status === Loader3D.Error)
                view.assetError("The prepared Portal scene could not be loaded.")
        }
    }
    Binding {
        target: portal.item
        property: "sceneSeconds"
        value: view.sceneSeconds
        when: portal.status === Loader3D.Ready
    }
}
