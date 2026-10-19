function [dT,q,ambient,coolant]=m2_flux(c,T,Q,speed)
% Every internal exchange is signed, equal and opposite at its two ends.
assert(all(isfinite(T)) && all(T>0),'m2:AbsoluteTemperature','Radiation requires positive absolute K');
assert(all(isfinite(Q)) && all(Q>=0) && speed>=0,'m2:Source','Nonnegative finite heating and speed required');
delta=T(c.from)-T(c.to);
q=(c.G0'+c.Gv'*sqrt(speed)).*delta+c.Rad'.*(T(c.from).^4-T(c.to).^4);
ambient=(c.AmbG0+c.AmbGv*sqrt(speed)).*(T-c.Tambient)+c.AmbRad.*(T.^4-c.Tambient^4);
coolant=c.CoolG.*(T-c.Tcoolant);
dT=(Q-c.B*q-ambient-coolant)./c.C;
end
