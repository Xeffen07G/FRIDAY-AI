import { memo } from 'react';

function AmbientBackground() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden bg-[#020304]">
      {/* Dark gradient base */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-900/10 via-[#020304] to-[#020304]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-cyan-900/10 via-transparent to-transparent" />
      
      {/* Subtle parallax/moving shapes - using opacity and transforms with radial gradients instead of heavy blur */}
      <div className="absolute top-[-20%] left-[-20%] w-[80%] h-[80%] bg-[radial-gradient(circle_at_center,_rgba(59,130,246,0.05)_0%,_transparent_50%)] rounded-full animate-slow-breath" style={{ animationDuration: '12s' }} />
      <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-[radial-gradient(circle_at_center,_rgba(6,182,212,0.05)_0%,_transparent_50%)] rounded-full animate-slow-breath" style={{ animationDuration: '15s' }} />
      
      {/* Moving grain overlay */}
      <div 
        className="absolute inset-0 opacity-[0.03]" 
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          mixBlendMode: 'overlay'
        }}
      />
    </div>
  );
}
export default memo(AmbientBackground);
