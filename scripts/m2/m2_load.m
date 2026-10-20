function c=m2_load(root,mode,overrides)
if nargin<2, mode='engineering'; end
if nargin<3, overrides=struct; end
assert(ismember(string(mode),["engineering","strict"]),'m2:Mode','Explicit mode required');
if strcmp(mode,'strict'), error('m2:EvidenceGap','No calibrated thermal resistance/cooling network is available.'); end
input=jsondecode(fileread(fullfile(root,'results','m2','inputs.json')));
assert(strcmp(input.configuration.metadata.baseline_commit,'9d545ab39a3efcce857573af74f7e325b74a2b15'));
c=m2_network(input.configuration,overrides); c.provenance=input.provenance; c.root=root;
end
