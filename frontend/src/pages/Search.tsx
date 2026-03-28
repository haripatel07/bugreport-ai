import React from 'react';

const SearchPage: React.FC = () => {
  return (
    <section className="panel reveal">
      <h2 className="card-title">Search</h2>
      <p style={{ color: 'var(--text-secondary)', marginTop: 0 }}>
        Dedicated cross-project search workspace is reserved for the next iteration.
      </p>
      <p style={{ color: 'var(--text-secondary)' }}>
        For now, use Analyze to run semantic similar-bug search in the recommendation pipeline.
      </p>
    </section>
  );
};

export default SearchPage;
