import { motion } from 'framer-motion';

export default function OrbCoreV2({ state = 'IDLE', className = '' }) {
  // Transitions mapped to spring 400-700ms
  const springConfig = { type: 'spring', stiffness: 80, damping: 20 };

  const stateVariants = {
    IDLE: { scale: [0.82, 0.85, 0.82], transition: { duration: 4, repeat: Infinity, ease: 'easeInOut' } },
    LISTENING: { scale: [1.02, 1.08, 1.02], transition: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' } },
    THINKING: { scale: 1, transition: springConfig },
    SPEAKING: { scale: [1, 1.1, 0.95, 1.05, 1], transition: { duration: 1.2, repeat: Infinity, ease: 'easeInOut' } },
    WORKING: { scale: 0.9, transition: springConfig }
  };

  const ringVariants = {
    IDLE: { scale: 1, opacity: 0, rotate: 0 },
    LISTENING: { scale: [1, 1.4], opacity: [0.2, 0], transition: { duration: 1.5, repeat: Infinity } },
    THINKING: { scale: 1.2, opacity: 0.15, rotate: 360, transition: { rotate: { duration: 8, repeat: Infinity, ease: 'linear' } } },
    SPEAKING: { scale: [1, 1.25], opacity: [0.3, 0], transition: { duration: 0.8, repeat: Infinity } },
    WORKING: { scale: 1.1, opacity: 0.4, rotate: -360, transition: { rotate: { duration: 3, repeat: Infinity, ease: 'linear' } } }
  };

  return (
    <div className={`relative flex items-center justify-center w-[150px] h-[150px] md:w-[180px] md:h-[180px] lg:w-[220px] lg:h-[220px] ${className}`}>
      
      {/* Layer 5: Breathing glow (using radial-gradient instead of heavy blur) */}
      <motion.div 
        className="absolute inset-[-40%] rounded-full"
        style={{ background: 'radial-gradient(circle at 50% 50%, rgba(59,130,246,0.16) 0%, transparent 70%)' }}
        variants={stateVariants}
        animate={state}
      />
      
      {/* Layer 4: Halo glow */}
      <motion.div 
        className="absolute inset-[-20%] rounded-full"
        style={{ background: 'radial-gradient(circle at 50% 50%, rgba(34,211,238,0.16) 0%, transparent 60%)' }}
        variants={stateVariants}
        animate={state}
      />
      
      {/* Layer 3: Outer Energy ring */}
      <motion.div
        className="absolute inset-[-10%] border border-blue-400/20 rounded-full"
        variants={ringVariants}
        animate={state}
        style={{ borderStyle: state === 'WORKING' ? 'dashed' : 'solid' }}
      />
      
      {/* Layer 1 & 2: Core sphere with internal rotation during thinking */}
      <motion.div
        className="absolute inset-8 rounded-full z-10 overflow-hidden"
        style={{
          background: 'radial-gradient(circle at 35% 35%, #7CEEFF 0%, #4F8BFF 45%, #05070A 95%)',
        }}
        variants={stateVariants}
        animate={state}
      >
        {state === 'THINKING' && (
           <motion.div 
             className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_50%_100%,_#ffffff_0%,_transparent_60%)]"
             animate={{ rotate: 360 }}
             transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
           />
        )}
      </motion.div>
    </div>
  );
}
