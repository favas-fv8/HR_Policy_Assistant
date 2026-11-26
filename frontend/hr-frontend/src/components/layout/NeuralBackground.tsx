import { useEffect, useRef } from 'react';

declare global {
  interface Window {
    THREE?: any;
  }
}

export default function NeuralBackground() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const THREE = window.THREE;
    const container = containerRef.current;
    if (!THREE || !container) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 400;
    camera.position.x = 100;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const particleCount = 600;
    const sphereRadius = 220;
    const maxDistance = 65;

    const positions = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    const colors = new Float32Array(particleCount * 3);

    const colorBase = new THREE.Color('#dcd9e8');
    const colorAccent = new THREE.Color('#f7d9d0');
    const colorSecondary = new THREE.Color('#a3a1f2');

    for (let i = 0; i < particleCount; i++) {
      const phi = Math.acos(-1 + (2 * i) / particleCount);
      const theta = Math.sqrt(particleCount * Math.PI) * phi;
      const r = sphereRadius + (Math.random() * 15 - 7.5);
      positions[i * 3] = r * Math.cos(theta) * Math.sin(phi);
      positions[i * 3 + 1] = r * Math.sin(theta) * Math.sin(phi);
      positions[i * 3 + 2] = r * Math.cos(phi);
      sizes[i] = Math.random() > 0.9 ? Math.random() * 4 + 2 : Math.random() * 1.5 + 0.5;
      let mixColor = colorBase;
      const rand = Math.random();
      if (rand > 0.95) mixColor = colorAccent;
      else if (rand > 0.85) mixColor = colorSecondary;
      colors[i * 3] = mixColor.r;
      colors[i * 3 + 1] = mixColor.g;
      colors[i * 3 + 2] = mixColor.b;
    }

    const particlesGeometry = new THREE.BufferGeometry();
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    particlesGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const particlesMaterial = new THREE.ShaderMaterial({
      uniforms: { color: { value: new THREE.Color(0xffffff) } },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        void main() {
          vColor = color;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = size * (300.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        void main() {
          float dist = length(gl_PointCoord - vec2(0.5));
          if (dist > 0.5) discard;
          float alpha = smoothstep(0.5, 0.1, dist);
          gl_FragColor = vec4(vColor, alpha * 0.7);
        }
      `,
      transparent: true,
      depthWrite: false,
    });

    const particleSystem = new THREE.Points(particlesGeometry, particlesMaterial);
    const linesGeometry = new THREE.BufferGeometry();
    const maxLines = particleCount * 5;
    const linePositions = new Float32Array(maxLines * 3 * 2);
    const lineColors = new Float32Array(maxLines * 3 * 2);
    linesGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    linesGeometry.setAttribute('color', new THREE.BufferAttribute(lineColors, 3));
    const linesMaterial = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.12, linewidth: 1 });
    const lineMesh = new THREE.LineSegments(linesGeometry, linesMaterial);

    const globeGroup = new THREE.Group();
    globeGroup.add(particleSystem);
    globeGroup.add(lineMesh);
    globeGroup.position.x = 150;
    scene.add(globeGroup);

    let mouseX = 0;
    let mouseY = 0;
    let raf = 0;
    const onMouseMove = (event: MouseEvent) => {
      mouseX = (event.clientX - window.innerWidth / 2) * 0.05;
      mouseY = (event.clientY - window.innerHeight / 2) * 0.05;
    };
    document.addEventListener('mousemove', onMouseMove);

    const animate = () => {
      raf = requestAnimationFrame(animate);
      globeGroup.rotation.y += 0.0008;
      globeGroup.rotation.x += 0.0003;
      const targetX = mouseX * 0.008;
      const targetY = mouseY * 0.008;
      globeGroup.rotation.y += 0.03 * (targetX - globeGroup.rotation.y);
      globeGroup.rotation.x += 0.03 * (targetY - globeGroup.rotation.x);

      let vertexpos = 0;
      let colorpos = 0;
      let numConnected = 0;
      const positionsArr = particlesGeometry.attributes.position.array as Float32Array;
      const colorsArr = particlesGeometry.attributes.color.array as Float32Array;

      for (let i = 0; i < particleCount; i++) {
        for (let j = i + 1; j < particleCount; j++) {
          const dx = positionsArr[i * 3] - positionsArr[j * 3];
          const dy = positionsArr[i * 3 + 1] - positionsArr[j * 3 + 1];
          const dz = positionsArr[i * 3 + 2] - positionsArr[j * 3 + 2];
          const distSq = dx * dx + dy * dy + dz * dz;
          if (distSq < maxDistance * maxDistance) {
            const alpha = 1.0 - Math.sqrt(distSq) / maxDistance;
            linePositions[vertexpos++] = positionsArr[i * 3];
            linePositions[vertexpos++] = positionsArr[i * 3 + 1];
            linePositions[vertexpos++] = positionsArr[i * 3 + 2];
            lineColors[colorpos++] = colorsArr[i * 3] * alpha;
            lineColors[colorpos++] = colorsArr[i * 3 + 1] * alpha;
            lineColors[colorpos++] = colorsArr[i * 3 + 2] * alpha;
            linePositions[vertexpos++] = positionsArr[j * 3];
            linePositions[vertexpos++] = positionsArr[j * 3 + 1];
            linePositions[vertexpos++] = positionsArr[j * 3 + 2];
            lineColors[colorpos++] = colorsArr[j * 3] * alpha;
            lineColors[colorpos++] = colorsArr[j * 3 + 1] * alpha;
            lineColors[colorpos++] = colorsArr[j * 3 + 2] * alpha;
            numConnected++;
            if (numConnected >= maxLines) break;
          }
        }
        if (numConnected >= maxLines) break;
      }

      linesGeometry.setDrawRange(0, numConnected * 2);
      linesGeometry.attributes.position.needsUpdate = true;
      linesGeometry.attributes.color.needsUpdate = true;
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      if (width < 1024) {
        camera.position.x = 0;
        globeGroup.position.x = 0;
        globeGroup.position.z = -100;
      } else {
        camera.position.x = 100;
        globeGroup.position.x = 150;
        globeGroup.position.z = 0;
      }
      camera.updateProjectionMatrix();
    };
    window.addEventListener('resize', onResize);
    onResize();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
      document.removeEventListener('mousemove', onMouseMove);
      renderer.dispose();
      particlesGeometry.dispose();
      particlesMaterial.dispose();
      linesGeometry.dispose();
      linesMaterial.dispose();
      if (container.contains(renderer.domElement)) container.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={containerRef} className="neural-bg" aria-hidden="true" />;
}
