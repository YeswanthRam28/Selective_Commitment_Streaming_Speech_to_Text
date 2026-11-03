import React from 'react';
import type { PolicyConfig, PolicyMode } from '../types';

interface ControlsProps {
  isListening: boolean;
  provider: 'whisper' | 'mock';
  config: PolicyConfig;
  onToggleProvider: (p: 'whisper' | 'mock') => void;
  onUpdateConfig: (cfg: Partial<PolicyConfig>) => void;
  onStartStreaming: () => void;
  onStopStreaming: () => void;
  onRunReplay: () => void;
  onClear: () => void;
  isReplaying: boolean;
}

export const Controls: React.FC<ControlsProps> = ({
  isListening,
  provider,
  config,
  onToggleProvider,
  onUpdateConfig,
  onStartStreaming,
  onStopStreaming,
  onRunReplay,
  onClear,
  isReplaying,
}) => {
  return (
    <div className="studio-card controls-card">
      <div className="controls-grid">
        {/* Policy Selector */}
        <div className="control-group">
          <label className="control-label" htmlFor="policy-select">Commitment Policy</label>
          <select
            id="policy-select"
            className="control-select"
            value={config.mode}
            disabled={isListening}
            onChange={(e) => onUpdateConfig({ mode: e.target.value as PolicyMode })}
          >
            <option value="selective_commitment">Selective Commitment (Proposed)</option>
            <option value="raw_streaming">Raw Streaming (Immediate Partial Baseline)</option>
            <option value="fixed_delay">Fixed Delay (N-lag Baseline)</option>
          </select>
        </div>

        {/* Recognizer Provider */}
        <div className="control-group">
          <label className="control-label" htmlFor="provider-select">Recognizer Adapter</label>
          <select
            id="provider-select"
            className="control-select"
            value={provider}
            disabled={isListening}
            onChange={(e) => onToggleProvider(e.target.value as 'whisper' | 'mock')}
          >
            <option value="whisper">OpenAI Whisper (On-Device GPU)</option>
            <option value="mock">Deterministic Synthetic Mock (Replay)</option>
          </select>
        </div>

        {/* Stability Threshold (Selective Commitment) */}
        {config.mode === 'selective_commitment' && (
          <div className="control-group">
            <label className="control-label" htmlFor="stability-input">
              Stability Threshold: {config.required_stability_updates} updates
            </label>
            <input
              id="stability-input"
              type="range"
              min={1}
              max={6}
              value={config.required_stability_updates}
              disabled={isListening}
              onChange={(e) =>
                onUpdateConfig({ required_stability_updates: parseInt(e.target.value, 10) })
              }
              className="control-slider"
            />
          </div>
        )}

        {/* Deadline Fallback (Selective Commitment) */}
        {config.mode === 'selective_commitment' && (
          <div className="control-group">
            <label className="control-label" htmlFor="deadline-input">
              Commitment Deadline: {config.max_provisional_duration_sec}s
            </label>
            <input
              id="deadline-input"
              type="range"
              min={0.5}
              max={5.0}
              step={0.5}
              value={config.max_provisional_duration_sec}
              disabled={isListening}
              onChange={(e) =>
                onUpdateConfig({ max_provisional_duration_sec: parseFloat(e.target.value) })
              }
              className="control-slider"
            />
          </div>
        )}

        {/* Fixed Delay Lag (Fixed Delay Baseline) */}
        {config.mode === 'fixed_delay' && (
          <div className="control-group">
            <label className="control-label" htmlFor="lag-input">
              Commitment Lag: {config.fixed_delay_updates} tokens
            </label>
            <input
              id="lag-input"
              type="range"
              min={1}
              max={8}
              value={config.fixed_delay_updates}
              disabled={isListening}
              onChange={(e) =>
                onUpdateConfig({ fixed_delay_updates: parseInt(e.target.value, 10) })
              }
              className="control-slider"
            />
          </div>
        )}
      </div>

      <div className="controls-actions">
        {!isListening ? (
          <button
            className="studio-btn btn-primary"
            onClick={onStartStreaming}
            disabled={isReplaying}
          >
            <span className="btn-icon">🎙️</span> Start Live Recognition
          </button>
        ) : (
          <button className="studio-btn btn-danger" onClick={onStopStreaming}>
            <span className="btn-icon">⏹️</span> Stop Recognition
          </button>
        )}

        <button
          className="studio-btn btn-secondary"
          onClick={onRunReplay}
          disabled={isListening || isReplaying}
        >
          <span className="btn-icon">▶️</span> Run Deterministic Replay
        </button>

        <button
          className="studio-btn btn-outline"
          onClick={onClear}
          disabled={isListening}
        >
          Clear Display
        </button>
      </div>
    </div>
  );
};
