// Headless I/O adapter for pinned wow.export; its parser/writer stay upstream.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const Module = require('module');
const { execFileSync } = require('child_process');
const root = path.resolve(process.argv[2]);
const out = path.resolve(process.argv[3]);
const id = Number(process.argv[4] || 7476464);
const expectedModelHash = 'fe30f3290cf2396684446a81ed48c4264277b6d6b5e6c153ee8ff9393863cab4';
fs.mkdirSync(out, { recursive: true });

global.nw = { App: { manifest: { version: '0.2.19' } } };
const core = { view: { config: {
    overwriteFiles: true, modelsExportAnimations: true, modelsExportTextures: true,
    modelsExportAlpha: true, pathFormat: 'posix', exportDirectory: out
} } };
function provide(file, value) {
    const filename = path.join(root, 'src/js', file + '.js');
    require.cache[filename] = { id: filename, filename, loaded: true, exports: value };
}
provide('core', core);
provide('log', { write: console.log });
provide('constants', { MAGIC: { MD21: 0x3132444d, MD20: 0x3032444d }, VERSION: '0.2.19' });
provide('casc/listfile', {
    getByID: () => undefined, getByFilename: () => 0,
    getByIDOrUnknown: (fileId, extension) => fileId + extension
});
provide('generics', {
    fileExists: async file => fs.existsSync(file),
    createDirectory: async directory => fs.promises.mkdir(directory, { recursive: true })
});
// BufferWrapper imports a WebP encoder for canvas exports. This path uses Qt's
// image decoder, never that encoder or a browser canvas.
const loadModule = Module._load;
Module._load = function (name, ...args) {
    if (name === 'webp-wasm') return { encode: () => { throw Error('Canvas encoding is unused'); } };
    return loadModule.call(this, name, ...args);
};
const BufferWrapper = require(path.join(root, 'src/js/buffer'));
const M2Exporter = require(path.join(root, 'src/js/3D/exporters/M2Exporter'));

async function download(kind, fileId, extension) {
    const file = path.join(out, fileId + '.' + extension);
    if (!fs.existsSync(file)) {
        const url = `https://wow.zamimg.com/modelviewer/live/${kind}/${fileId}.${extension}`;
        let lastError;
        for (let attempt = 0; attempt < 3; attempt++) {
            try {
                const response = await fetch(url, { signal: AbortSignal.timeout(30000) });
                if (!response.ok) throw Error(`${url}: HTTP ${response.status}`);
                const data = Buffer.from(await response.arrayBuffer());
                if (!data.length) throw Error(`Empty asset: ${url}`);
                fs.writeFileSync(file + '.partial', data);
                fs.renameSync(file + '.partial', file);
                return file;
            } catch (error) { lastError = error; }
        }
        throw lastError;
    }
    return file;
}

// The pinned housing model has one internal idle sequence, no external skeleton.
core.view.casc = { getFile: async fileId => new BufferWrapper(
    fs.readFileSync(await download('skin', fileId, 'skin'))
) };

async function main() {
    if (id !== 7476464) throw Error('This adapter is scoped to housing Portal 7476464');
    const data = fs.readFileSync(await download('m2', id, 'm2'));
    if (crypto.createHash('sha256').update(data).digest('hex') !== expectedModelHash)
        throw Error('Source model changed. Review materials before updating the pinned hash.');
    const exporter = new M2Exporter(new BufferWrapper(data), [], id);
    await exporter.m2.load();
    const model = exporter.m2;
    if (model.skeletonFileID || model.vertices.length / 3 !== 16545)
        throw Error('Unexpected model topology or external skeleton');
    const textures = [...new Set(model.textures.map(texture => texture.fileDataID).filter(Boolean))];
    await Promise.all(textures.map(texture => download('textures', texture, 'webp')));
    exporter.exportTextures = async () => {
        const map = new Map();
        for (const texture of textures) {
            const png = path.join(out, texture + '.png');
            execFileSync(process.env.HEARTHKEEPER_PYTHON || 'python', [
                '-c', 'from PySide6.QtGui import QImage; import sys; image=QImage(sys.argv[1]); assert not image.isNull(); assert image.save(sys.argv[2])',
                path.join(out, texture + '.webp'), png
            ]);
            map.set(texture, { matName: texture + '.png', matPathRelative: texture + '.png', matPath: png });
        }
        return map;
    };
    await exporter.exportAsGLTF(path.join(out, 'portal.gltf'), { isCancelled: () => false }, 'gltf');
    const skin = await model.getSkin(0);
    fs.writeFileSync(path.join(out, 'source-metadata.json'), JSON.stringify({
        fileDataID: id, materials: model.materials, textures: model.textures.map(texture => texture.fileDataID),
        textureCombos: model.textureCombos, textureTransforms: model.textureTransforms,
        textureTransformsLookup: model.textureTransformsLookup, textureWeights: model.textureWeights,
        transparencyLookup: model.transparencyLookup, colors: model.colors,
        submeshes: skin.subMeshes, textureUnits: skin.textureUnits
    }, null, 2));
    console.log('Export complete:', out);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
