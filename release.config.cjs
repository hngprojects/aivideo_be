module.exports = {
  branches: [
    { name: 'main' },
    { name: 'staging', prerelease: 'rc' },
  ],
  plugins: [
    '@semantic-release/commit-analyzer',
    '@semantic-release/release-notes-generator',
    [
      '@semantic-release/npm',
      { npmPublish: false },
    ],
    [
      '@semantic-release/github',
      {
        successComment: false,
        failComment: false,
        failTitle: false,
        labels: false,
        releasedLabels: false,
        addReleases: 'bottom'
      },
    ],
    [
      '@semantic-release/git',
      {
        assets: ['package.json'],
        message: 'chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}',
      },
    ],
  ],
  onError: (error, { errors }) => {
    // Ignore "Not Found" errors (including issue not found)
    if (error.name === 'AggregateError') {
      return errors.filter(err => err.type !== 'NOT_FOUND');
    }
    return error;
  },
};
