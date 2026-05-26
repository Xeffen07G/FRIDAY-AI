import { motion } from 'framer-motion';

export default function OrbCore({ state = 'IDLE', className = '' }) {
  // Define animation states based on ENZO's current activity
  const variants = {
    IDLE: {
      scale: [1, 0.97, 1],
      opacity: [0.8, 0.5, 0.8],
      boxShadow: [
        '0 0 40px rgba(79, 139, 255, 0.1)',
        '0 0 20px rgba(79, 139, 255, 0.05)',
        '0 0 40px rgba(79, 139, 255, 0.1)',
      ],
      transition: { duration: 4, repeat: Infinity, ease: 'easeInOut' }
    },
    LISTENING: {
      scale: [1, 1.1, 1],
      opacity: [0.9, 1, 0.9],
      boxShadow: [
        '0 0 60px rgba(79, 139, 255, 0.2)',
        '0 0 80px rgba(124, 238, 255, 0.3)',
        '0 0 60px rgba(79, 139, 255, 0.2)',
      ],
      transition: { duration: 2, repeat: Infinity, ease: 'easeInOut' }
    },
    THINKING: {
      rotate: [0, 360],
      scale: [0.9, 0.95, 0.9],
      boxShadow: [
        '0 0 40px rgba(79, 139, 255, 0.3)',
        '0 0 60px rgba(124, 238, 255, 0.1)',
        '0 0 40px rgba(79, 139, 255, 0.3)',
      ],
      transition: { rotate: { duration: 8, repeat: Infinity, ease: 'linear' }, scale: { duration: 2, repeat: Infinity, ease: 'easeInOut' } }
    },
    STREAMING: {
      scale: [0.95, 1.05, 0.95],
      opacity: [0.8, 1, 0.8],
      boxShadow: [
        '0 0 50px rgba(124, 238, 255, 0.2)',
        '0 0 90px rgba(79, 139, 255, 0.4)',
        '0 0 50px rgba(124, 238, 255, 0.2)',
      ],
      transition: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' }
    },
    SPEAKING: {
      scale: [1, 1.2, 0.9, 1.1, 1],
      opacity: 1,
      boxShadow: '0 0 80px rgba(124, 238, 255, 0.4)',
      transition: { duration: 0.8, repeat: Infinity, ease: 'easeInOut' } // Fast audio-reactive approximation
    },
    EXECUTING: {
      scale: 0.7,
      opacity: 1,
      boxShadow: '0 0 100px rgba(255, 255, 255, 0.5)',
      transition: { duration: 0.5, ease: 'easeOut' }
    }
  };

  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <motion.div
        className="w-32 h-32 rounded-full z-10"
        style={{
          background: 'radial-gradient(circle at 30% 30%, #7CEEFF 0%, #4F8BFF 40%, #05070A 90%)',
          border: '1px solid rgba(124, 238, 255, 0.1)'
        }}
        variants={variants}
        animate={state}
      />
      
      {/* Optional particle rings for THINKING state */}
      {state === 'THINKING' && (
        <motion.div
          className="absolute w-40 h-40 rounded-full border-t-2 border-l-2 border-blue-500/20"
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
        />
      )}
      {state === 'LISTENING' && (
        <motion.div
          className="absolute w-48 h-48 rounded-full border border-blue-400/10"
          animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeOut' }}
        />
      )}
    </div>
  );
}
