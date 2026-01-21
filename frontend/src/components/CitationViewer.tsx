"use client";

import React, { useState, useRef, useEffect } from "react";

// Types
export interface EvidenceAtom {
  evidence_id: string;
  evidence_type: string;
  source_system: string;
  document_name: string;
  content_excerpt: string;
  confidence: number;
}

interface CitationPopoverProps {
  evidenceId: string;
  atoms: EvidenceAtom[];
  onClose: () => void;
  position: { x: number; y: number };
}

// Citation Popover Component (like Zotero popup)
const CitationPopover: React.FC<CitationPopoverProps> = ({
  evidenceId,
  atoms,
  onClose,
  position,
}) => {
  const popoverRef = useRef<HTMLDivElement>(null);
  const atom = atoms.find((a) => a.evidence_id === evidenceId);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  if (!atom) {
    return (
      <div
        ref={popoverRef}
        className="fixed z-50 bg-gray-900 border border-red-500/50 rounded-xl p-4 shadow-2xl max-w-md"
        style={{ left: position.x, top: position.y }}
      >
        <p className="text-red-400 text-sm">Evidence not found: {evidenceId}</p>
        <button onClick={onClose} className="text-gray-400 text-xs mt-2 hover:text-white">
          Close
        </button>
      </div>
    );
  }

  return (
    <div
      ref={popoverRef}
      className="fixed z-50 bg-gradient-to-br from-gray-900 to-gray-800 border border-emerald-500/50 rounded-xl p-4 shadow-2xl max-w-lg animate-in fade-in slide-in-from-bottom-2 duration-200"
      style={{ left: Math.min(position.x, window.innerWidth - 450), top: position.y }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-emerald-400 font-mono text-sm font-bold">{atom.evidence_id}</span>
          <span className="bg-emerald-500/20 text-emerald-300 text-xs px-2 py-0.5 rounded">
            {atom.evidence_type.replace(/_/g, " ")}
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Source info */}
      <div className="flex items-center gap-4 text-xs text-gray-400 mb-3">
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          {atom.source_system}
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {atom.document_name}
        </span>
      </div>

      {/* Content */}
      <div className="bg-gray-800/50 rounded-lg p-3 border-l-4 border-emerald-500">
        <p className="text-white text-sm leading-relaxed">{atom.content_excerpt}</p>
      </div>

      {/* Confidence */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Confidence:</span>
          <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                atom.confidence >= 0.9
                  ? "bg-emerald-500"
                  : atom.confidence >= 0.7
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
              style={{ width: `${atom.confidence * 100}%` }}
            />
          </div>
          <span className="text-xs text-gray-300">{(atom.confidence * 100).toFixed(0)}%</span>
        </div>
        <span className="text-xs text-emerald-400">✓ Verified Source</span>
      </div>
    </div>
  );
};

// Inline Citation Component (the clickable [EV-xxx] marker)
interface InlineCitationProps {
  evidenceId: string;
  atoms: EvidenceAtom[];
}

export const InlineCitation: React.FC<InlineCitationProps> = ({ evidenceId, atoms }) => {
  const [showPopover, setShowPopover] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);

  const handleClick = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setPosition({ x: rect.left, y: rect.bottom + 8 });
      setShowPopover(true);
    }
  };

  const atom = atoms.find((a) => a.evidence_id === evidenceId);
  const isValid = !!atom;

  return (
    <>
      <button
        ref={buttonRef}
        onClick={handleClick}
        className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs font-mono transition-all duration-150 ${
          isValid
            ? "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 hover:text-emerald-300"
            : "bg-red-500/20 text-red-400 hover:bg-red-500/30"
        }`}
        title={atom?.content_excerpt || "Evidence not found"}
      >
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        {evidenceId.replace("EV-", "")}
      </button>
      {showPopover && (
        <CitationPopover
          evidenceId={evidenceId}
          atoms={atoms}
          onClose={() => setShowPopover(false)}
          position={position}
        />
      )}
    </>
  );
};

// Parse text and replace [EV-xxx] with clickable citations
interface CitedTextProps {
  text: string;
  atoms: EvidenceAtom[];
  className?: string;
}

export const CitedText: React.FC<CitedTextProps> = ({ text, atoms, className = "" }) => {
  // Parse the text and split by citation markers
  const parts = text.split(/(\[EV-[a-f0-9]+\])/gi);

  return (
    <span className={className}>
      {parts.map((part, index) => {
        const match = part.match(/\[EV-([a-f0-9]+)\]/i);
        if (match) {
          const evidenceId = `EV-${match[1]}`;
          return <InlineCitation key={index} evidenceId={evidenceId} atoms={atoms} />;
        }
        return <span key={index}>{part}</span>;
      })}
    </span>
  );
};

// Full Narrative Section Component
interface NarrativeSectionProps {
  title: string;
  content: string;
  atoms: EvidenceAtom[];
  evidenceIds: string[];
  icon?: React.ReactNode;
  borderColor?: string;
}

export const NarrativeSection: React.FC<NarrativeSectionProps> = ({
  title,
  content,
  atoms,
  evidenceIds,
  icon,
  borderColor = "border-blue-500",
}) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className={`bg-gray-800/50 rounded-xl border-l-4 ${borderColor} overflow-hidden`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          {icon && <span className="text-2xl">{icon}</span>}
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">
            {evidenceIds.length} citations
          </span>
        </div>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {expanded && (
        <div className="px-4 pb-4">
          <div className="text-gray-200 leading-relaxed whitespace-pre-wrap">
            <CitedText text={content} atoms={atoms} />
          </div>
        </div>
      )}
    </div>
  );
};

// Evidence Library Panel (like Zotero sidebar)
interface EvidenceLibraryProps {
  atoms: EvidenceAtom[];
  highlightedIds?: string[];
}

export const EvidenceLibrary: React.FC<EvidenceLibraryProps> = ({
  atoms,
  highlightedIds = [],
}) => {
  const [search, setSearch] = useState("");
  const [selectedType, setSelectedType] = useState<string | null>(null);

  const types = [...new Set(atoms.map((a) => a.evidence_type))];

  const filteredAtoms = atoms.filter((atom) => {
    const matchesSearch =
      search === "" ||
      atom.content_excerpt.toLowerCase().includes(search.toLowerCase()) ||
      atom.evidence_id.toLowerCase().includes(search.toLowerCase());
    const matchesType = selectedType === null || atom.evidence_type === selectedType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="bg-gray-800/50 rounded-xl border border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-3">
          <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          Evidence Library
        </h3>

        {/* Search */}
        <input
          type="text"
          placeholder="Search evidence..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
        />

        {/* Type Filter */}
        <div className="flex flex-wrap gap-2 mt-3">
          <button
            onClick={() => setSelectedType(null)}
            className={`text-xs px-2 py-1 rounded transition-colors ${
              selectedType === null
                ? "bg-emerald-500 text-white"
                : "bg-gray-700 text-gray-300 hover:bg-gray-600"
            }`}
          >
            All ({atoms.length})
          </button>
          {types.map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                selectedType === type
                  ? "bg-emerald-500 text-white"
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
            >
              {type.replace(/_/g, " ")} ({atoms.filter((a) => a.evidence_type === type).length})
            </button>
          ))}
        </div>
      </div>

      {/* Evidence List */}
      <div className="max-h-96 overflow-y-auto">
        {filteredAtoms.map((atom) => (
          <div
            key={atom.evidence_id}
            className={`p-3 border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors ${
              highlightedIds.includes(atom.evidence_id) ? "bg-emerald-500/10" : ""
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-mono text-xs text-emerald-400">{atom.evidence_id}</span>
              <span className="text-xs text-gray-500">{atom.source_system}</span>
            </div>
            <p className="text-sm text-gray-200 line-clamp-2">{atom.content_excerpt}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs bg-gray-700/50 text-gray-400 px-1.5 py-0.5 rounded">
                {atom.evidence_type.replace(/_/g, " ")}
              </span>
              <span className="text-xs text-gray-500">
                {(atom.confidence * 100).toFixed(0)}% confidence
              </span>
            </div>
          </div>
        ))}
        {filteredAtoms.length === 0 && (
          <div className="p-6 text-center text-gray-500">No evidence found</div>
        )}
      </div>
    </div>
  );
};

