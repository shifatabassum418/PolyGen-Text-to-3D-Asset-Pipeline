import { Component, Suspense, useMemo } from "react";
import { Canvas, useLoader } from "@react-three/fiber";
import { Bounds, Grid, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader.js";
import { MTLLoader } from "three/examples/jsm/loaders/MTLLoader.js";

function ObjModel({ url }) {
  const obj = useLoader(OBJLoader, url);
  const model = useMemo(() => {
    const clone = obj.clone(true);
    clone.traverse((child) => {
      if (!child.isMesh) return;
      child.geometry.computeVertexNormals();
      child.material = new THREE.MeshStandardMaterial({
        color: "#b9bec7",
        roughness: 0.6,
        metalness: 0.1,
        vertexColors: !!child.geometry.attributes.color,
        side: THREE.DoubleSide,
      });
    });
    return clone;
  }, [obj]);
  return <primitive object={model} />;
}

// Loads model.mtl first so OBJLoader can bind the baked texture; both files sit in the same job folder.
function TexturedModel({ objUrl, mtlUrl }) {
  const base = mtlUrl.slice(0, mtlUrl.lastIndexOf("/") + 1);
  const materials = useLoader(MTLLoader, mtlUrl, (loader) => loader.setResourcePath(base));
  const obj = useLoader(OBJLoader, objUrl, (loader) => {
    materials.preload();
    loader.setMaterials(materials);
  });
  const model = useMemo(() => {
    const clone = obj.clone(true);
    clone.traverse((child) => {
      if (!child.isMesh) return;
      child.geometry.computeVertexNormals();
      const mats = Array.isArray(child.material) ? child.material : [child.material];
      mats.forEach((m) => {
        if (m.map) m.map.colorSpace = THREE.SRGBColorSpace;
        m.side = THREE.DoubleSide;
        m.needsUpdate = true;
      });
    });
    return clone;
  }, [obj]);
  return <primitive object={model} />;
}

class ModelBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error) { this.props.onError?.(`Could not load the model: ${error?.message || error}`); }
  componentDidUpdate(prev) { if (prev.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: null }); }
  render() { return this.state.error ? null : this.props.children; }
}

export default function Viewer({ objUrl, mtlUrl, onError }) {
  return (
    <Canvas camera={{ position: [1.6, 1.1, 1.8], fov: 40 }} dpr={[1, 2]}>
      <color attach="background" args={["#12151a"]} />
      <ambientLight intensity={0.55} />
      <directionalLight position={[3, 5, 4]} intensity={2.2} />
      <directionalLight position={[-4, 2, -3]} intensity={0.8} color="#9db4ff" />
      <Grid position={[0, -0.51, 0]} args={[10, 10]} cellColor="#2a303a" sectionColor="#3a4352" fadeDistance={8} infiniteGrid />
      <ModelBoundary resetKey={objUrl + (mtlUrl || "")} onError={onError}>
        <Suspense fallback={null}>
          {objUrl && (
            <Bounds fit clip observe margin={1.3}>
              {mtlUrl ? <TexturedModel objUrl={objUrl} mtlUrl={mtlUrl} /> : <ObjModel url={objUrl} />}
            </Bounds>
          )}
        </Suspense>
      </ModelBoundary>
      <OrbitControls makeDefault enableDamping />
    </Canvas>
  );
}
