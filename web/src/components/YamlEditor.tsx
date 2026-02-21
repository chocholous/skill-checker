import { useCallback, useEffect, useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { yaml } from '@codemirror/lang-yaml';
import { api } from '../api/client';

interface Props {
  sourceFile: string;
  onSaved?: () => void;
}

export function YamlEditor({ sourceFile, onSaved }: Props) {
  const [content, setContent] = useState('');
  const [original, setOriginal] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getRawYaml(sourceFile).then(data => {
      setContent(data.content);
      setOriginal(data.content);
      setLoading(false);
    }).catch(e => {
      setError(String(e));
      setLoading(false);
    });
  }, [sourceFile]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      await api.updateYaml(sourceFile, content);
      setOriginal(content);
      setSuccess(true);
      onSaved?.();
      setTimeout(() => setSuccess(false), 2000);
    } catch (e: unknown) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  }, [sourceFile, content, onSaved]);

  // Cmd+S to save
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleSave]);

  if (loading) return <div className="p-4 text-gray-500">Loading...</div>;

  const isDirty = content !== original;

  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-gray-100 border-b">
        <span className="font-mono text-sm text-gray-600">{sourceFile}</span>
        <div className="flex items-center gap-2">
          {isDirty && <span className="text-xs text-amber-600">Unsaved changes</span>}
          {success && <span className="text-xs text-green-600">Saved!</span>}
          <button
            onClick={handleSave}
            disabled={saving || !isDirty}
            className="px-3 py-1 text-sm rounded bg-blue-600 text-white disabled:opacity-40 hover:bg-blue-700"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
      {error && (
        <div className="px-3 py-2 bg-red-50 text-red-700 text-sm border-b">{error}</div>
      )}
      <CodeMirror
        value={content}
        onChange={setContent}
        extensions={[yaml()]}
        height="400px"
        basicSetup={{ lineNumbers: true, foldGutter: true }}
      />
    </div>
  );
}
