function render_saved_plots
% Layout-only refresh; no thermal calculations or test results are overwritten.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));c=m2_load(root);
s=load(fullfile(root,'results','m2','m2_results.mat'),'archivedResults','sensitivity','comparison');
m2_plots(c,s.archivedResults,s.sensitivity,s.comparison,fullfile(root,'results','m2'));
end
