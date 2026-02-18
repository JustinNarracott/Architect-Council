import HelpSection from '@/components/help/HelpSection';
import HelpCallout from '@/components/help/HelpCallout';
import HelpBreadcrumb from '@/components/help/HelpBreadcrumb';

export default function RAGChatHelp() {
  return (
    <>
      <HelpBreadcrumb items={[{ label: 'RAG Chat' }]} />
      <div className="mb-8">
        <h1 className="font-headline text-2xl text-accent-blue tracking-wide mb-2">RAG Chat</h1>
        <p className="text-text-secondary text-sm">
          Ask follow-up questions about a reviewed codebase using retrieval-augmented generation.
        </p>
      </div>

      <HelpSection id="what-is-rag" title="What Is RAG Chat?">
        <p>
          After a codebase review completes, the repository is indexed and stored in a local
          vector database (ChromaDB). RAG Chat lets you ask natural language questions about
          the code, and the system retrieves the most relevant code chunks to ground its answers.
        </p>
        <p>
          This means answers are based on the actual source code — not hallucinated from general
          training data. Each response includes source references showing which files and line
          numbers were used.
        </p>
      </HelpSection>

      <HelpSection id="asking-questions" title="Asking Questions">
        <p>
          The chat panel appears after a codebase review completes. Type your question and press
          Enter or click Send. The response streams in real time with source badges showing the
          file, line range, and code element that informed the answer.
        </p>
        <p>Good questions to try:</p>
        <ul className="list-disc list-inside space-y-1 text-text-secondary ml-2">
          <li>&quot;How is authentication handled in this project?&quot;</li>
          <li>&quot;What database models are defined and how do they relate?&quot;</li>
          <li>&quot;Are there any hardcoded configuration values?&quot;</li>
          <li>&quot;Explain the error handling strategy used in the API routes.&quot;</li>
          <li>&quot;What testing patterns are used?&quot;</li>
        </ul>
        <HelpCallout type="tip">
          Be specific. &quot;How does the user service validate email addresses?&quot; will get a
          better answer than &quot;Tell me about validation.&quot;
        </HelpCallout>
      </HelpSection>

      <HelpSection id="how-indexing-works" title="How Indexing Works">
        <p>
          When a codebase review starts, the repository is processed through an indexing pipeline:
        </p>
        <ol className="list-decimal list-inside space-y-2 text-text-secondary ml-2">
          <li>
            <strong className="text-text-primary">AST Chunking</strong> — Source files are parsed into
            their abstract syntax tree and split into meaningful chunks (functions, classes, modules)
            rather than arbitrary line ranges.
          </li>
          <li>
            <strong className="text-text-primary">Embedding</strong> — Each chunk is converted into a
            vector embedding that captures its semantic meaning.
          </li>
          <li>
            <strong className="text-text-primary">Storage</strong> — Embeddings are stored in ChromaDB,
            a local vector database running inside the Docker container.
          </li>
          <li>
            <strong className="text-text-primary">Retrieval</strong> — When you ask a question, the
            system finds the most semantically similar chunks and includes them as context for the
            language model.
          </li>
        </ol>
        <HelpCallout type="note">
          The index is ephemeral — it exists only for the current review session. Starting a new
          review on a different repository replaces the previous index.
        </HelpCallout>
      </HelpSection>
    </>
  );
}
