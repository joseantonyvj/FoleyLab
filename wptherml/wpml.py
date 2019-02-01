#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 10 21:07:22 2018

@author: jay
"""
from wptherml import tmm
from wptherml import colorlib
from wptherml import stpvlib
from wptherml.datalib import datalib
from matplotlib import pyplot as plt
from scipy import integrate

import numpy as np
class multilayer:
    
    ### initializer
    #def __init__(self, mode, inputfile):
    def __init__(self, args):
        ### set up some default attributes
        self.result = 1
        self.mode = args.get('mode')
        #print(" Mode is ",self.mode)
        
        ### There might not always be an input file..
        ### need to make sure we think about to handle this
        self.inputfile = args.get('file')
        
        ### Set default values for all attributes
        ###that are required for actually running
        ### different calculations... will check for
        ### user input on these later
        self.pol = 'p'
        self.th = 0
        ### default temperature is 300 K, aka ambient temp
        ### this is not a relevant temp for STPV applications
        self.T = 300
        ### default bandgap wavelength is 2254e-9 m, good value for InGaAsSb
        self.lbg = 2254e-9
        ### default PV is InGaAsSb
        self.PV = "InGaAsSb"
        ### default Temperature of PV cell is 25 deg C 
        ### or 298 K
        self.T_cell = 298
        ### default solar concentration for STPV absorber
        self.solarconc = 600
        ### default is to not use explicit angle dependence of emissivity, etc
        self.explicit_angle = 0
        ### by default, degree of G-L polynomial will not be needed since explicit angle dependence
        ### is not the default but 
        ### we will set it at 7 anyway for now
        self.deg = 7
        
        ### relates to SPP and PA resonances
        self.SPP_Resonance = 0+0j
        self.PA_Resonance = 0+0j
        ### attributes that relate to which quantities should
        ### be computed... the default will be 
        ### only to compute the Fresnel reflection, transmission,
        ### and absorption/emissivity for a structure
        ### all further options must be specified by user
        ### typically stpv emitters will be designed
        ### using different criteria than absorbers
        ### so the two applications will be treated independently
        self.stpv_emitter_calc = 0
        self.stpv_absorber_calc = 0
        ### note there could be a third section for an integrated absorber/emitter
        ### but some thought is required 
        self.cooling_calc = 0
        self.lightbulb_calc = 0
        self.spp_calc = 0
        self.color_calc = 0
        self.fresnel_calc = 1
        self.explicit_angle = 0
        self.resonance = 0
 
        
        ### Three modes currently supported... 
        ### at the very least after calling the methods
        ### associated with each mode, a structure will
        ### be defined (including RI of each layer for a user-specified
        ### range of wavelengths) and calculation type(s) will be selected
        
        ### interactive mode will prompt user for input that
        ### defines the calculation
        if self.mode=='Interactive':
            self.interactive_structure()
            
        ### batch mode reads input from a file
        elif self.mode=='Batch':
            self.batch_structure(self.inputfile)
        
        ### inline mode takes a dictionary (args)
        ### to define input options
        elif self.mode=='Inline':
            self.inline_structure(args)
            
        ### Default is interactive mode!
        else:
            self.interactive_structure()
            
        ### Now that structure is defined and we have the lambda array, 
        ### allocate other arrays!
        ### Always need normal arrays
        self.Reflectivity = np.zeros(len(self.lam))
        self.Transmissivity = np.zeros(len(self.lam))
        self.Emissivity = np.zeros(len(self.lam))
        self.TE = np.zeros(len(self.lam))
        
        ### In some cases the user may wish to compute
        ### R, T, or eps vs angle at a specific wavelength
        ### we will allocate three arrays for these cases
        ### with a resolution of 0.5 degrees... i.e. they are small!
        self.r_vs_theta = np.zeros(180)
        self.t_vs_theta = np.zeros(180)
        self.eps_vs_theta = np.zeros(180)
        self.theta_array = np.linspace(0,np.pi/2., 180)
        ### If users selects explicit_angle option, we 
        ### need arrays for R, T, and eps as a function of angle
        ### and polarization, as well
        if (self.explicit_angle):
            ### range is 0 to thetaC
            a = 0
            b = np.pi/2.
            self.x, self.w = np.polynomial.legendre.leggauss(self.deg)
            self.t = 0.5*(self.x + 1)*(b - a) + a
            self.w = self.w * 0.5 * (b-a)
            
            self.Reflectivity_p = np.zeros((self.deg,len(self.lam)))
            self.Reflectivity_s = np.zeros((self.deg,len(self.lam)))
            self.Transmissivity_p = np.zeros((self.deg,len(self.lam)))
            self.Transmissivity_s = np.zeros((self.deg,len(self.lam)))
            self.Emissivity_p = np.zeros((self.deg,len(self.lam)))
            self.Emissivity_s = np.zeros((self.deg,len(self.lam)))
            self.TE_p = np.zeros((self.deg,len(self.lam)))
            self.TE_s = np.zeros((self.deg,len(self.lam)))


            
        ### Get all far-field Fresnel-related quantities:
        ### Reflectivity, Transmissivity, and Absorptivity/Emissivity spectra
        ### Always call the normal version
        self.Fresnel()
        
        ### If user selected explict_angle option, call the EA methods as well
        if (self.explicit_angle):
            ### get the Reflectivity, Transmissivity, and Absorptivity/Emissivity
            ### at the angles from the Gauss-Legendre grid
            self.Fresnel_EA()
            ### Get the thermal emission at the angles from the
            ### Gauss-Legendre grid
            self.ThermalEmission_EA()
        


        ### stpv_calc cooling_calc lightbulb_calc color_calc all
        ### require BB spectrum / thermal emission spectrum
        if (self.stpv_emitter_calc or self.stpv_absorber_calc or self.cooling_calc or self.lightbulb_calc or self.color_calc):
            ### The ThermalEmission() method automatically calculates the BB spectrum
            ### and stores it to self.BBs
            self.ThermalEmission()

        #self.ThermalColor()
        ### now that default quantitites have been calculated, start
        ### looking at optional quantities
        if (self.stpv_emitter_calc):
            
            self.stpv_se()
            self.stpv_pd()
            self.stpv_etatpv()
            
        if (self.stpv_absorber_calc):
        
            if (self.explicit_angle):
                self.stpv_etaabs_ea()
            else:
                self.stpv_etaabs()
            
        if (self.color_calc):
            
            print("color")
            #self.AmbientColor()
            #self.ThermalColor()
            
        if (self.lightbulb_calc):
            
            ### Luminous efficiency and efficacy calcs here
            self.LuminousEfficiency()
            self.LuminousEfficacy()
            ### need a method for computing luminous efficacy
        
        if (self.cooling_calc):
            print("cooling")
            
            ### need a method for computing the cooling power
            
            ### Might want to store the result(s) somehow in something
            ### other than the attributes... though it seems a little redundant 
            ### to do so
            #self.result = {}
            
        
            
            
            
            

        
    ### Methods to compute all Fresnel quantities at once!
    ### to compute the emissivity, one needs to compute R and T anyway
    ### so  might as well compute them all at once
    ''' FLAGGED!  Rename method with accepted convention! '''
    def Fresnel(self):
        nc = np.zeros(len(self.d),dtype=complex)
        for i in range(0,len(self.lam)):
            for j in range(0,len(self.d)):
                nc[j] = self.n[j][i]
                
            k0 = np.pi*2/self.lam[i]
            ### get transfer matrix for this k0, th, pol, nc, and d
            M = tmm.tmm(k0, self.th, self.pol, nc, self.d)
            ### get t amplitude
            t = 1./M["M11"]
            ### get incident/final angle
            ti = M["theta_i"]
            tL = M["theta_L"]
            ### get geometric factor associated with transmission
            fac = nc[len(self.d)-1]*np.cos(tL)/(nc[0]*np.cos(ti))
            ### get reflection amplitude
            r = M["M21"]/M["M11"]
            ### get Reflectivity
            self.Reflectivity[i] = np.real(r * np.conj(r))
            ### get Transmissivity
            self.Transmissivity[i] = np.real(t*np.conj(t)*fac)
            self.Emissivity[i] = 1 - self.Reflectivity[i] - self.Transmissivity[i]

        return 1
    
    def angular_fresnel(self, lambda_0):
        ### create an array for RI of each layer at the
        ### desired wavelength
        nc = np.zeros(len(self.d),dtype=complex)
        ### get RI for each layer and store it in nc array
        for i in range(0,len(self.matlist)):
            nc[i] = datalib.Material_RI(lambda_0, self.matlist[i])
        k0 = np.pi*2/lambda_0
        i=0
        for thetai in self.theta_array:
            ### increment by 1/2 degrees
            M = tmm.tmm(k0, thetai, self.pol, nc, self.d)
            
            t = 1./M["M11"]
            
            ### get incident/final angle
            ti = M["theta_i"]
            tL = M["theta_L"]
            ### get geometric factor associated with transmission
            fac = nc[len(self.d)-1]*np.cos(tL)/(nc[0]*np.cos(ti))
            ### get reflection amplitude
            r = M["M21"]/M["M11"]
            ### get Reflectivity
            self.r_vs_theta[i] = np.real(r * np.conj(r))
            ### get Transmissivity
            self.t_vs_theta[i] = np.real(t*np.conj(t)*fac)
            self.eps_vs_theta[i] = 1 - self.r_vs_theta[i] - self.t_vs_theta[i]
            i = i+1
            
        return 1

    ### In case users ONLY wants reflectivity
    def reflection(self):
        nc = np.zeros(len(self.d),dtype=complex)
        for i in range(0,len(self.lam)):
            for j in range(0,len(self.d)):
                nc[j] = self.n[j][i]
                
            k0 = np.pi*2/self.lam[i]
            self.Reflectivity[i] = tmm.Reflect(k0, self.th, self.pol, nc, self.d)

        return 1
    ### In case user ONLY wants transmissivity
    def transmission(self):
        nc = np.zeros(len(self.d),dtype=complex)
        for i in range(0,len(self.lam)):
            for j in range(0,len(self.d)):
                nc[j] = self.n[j][i]
                
            k0 = np.pi*2/self.lam[i]
            self.Transmissivity[i] = tmm.Trans(k0, self.th, self.pol, nc, self.d)

        return 1
    
    ### Fresnel methods when explicit angle-averaging is requested...
    ### Need to have FOM methods to accompany this
    ''' FLAGGED!  Rename method with accepted convention! '''
    def Fresnel_EA(self):
        ### The angles come from Gauss-Legendre quadrature
        nc = np.zeros(len(self.d),dtype=complex)
        ### outter loop is over wavelength - this modulates the RI
        for i in range(0,len(self.lam)):
            k0 = np.pi*2/self.lam[i]
            ### for given wavelength, the stack will have the following set of RIs
            for j in range(0,len(self.d)):
                nc[j] = self.n[j][i]
            
            ### iterate over angles
            for j in range(0,len(self.t)):
                ### for given angle, k0, pol, nc, and d
                ### compute M
                Mp = tmm.tmm(k0, self.t[j], 'p', nc, self.d)
                Ms = tmm.tmm(k0, self.t[j], 's', nc, self.d)
                ### get amplitudes and related quantities from M dictionaries
                tp = 1./Mp["M11"]
                ts = 1./Ms["M11"]
                tp_i = Mp["theta_i"]
                ts_i = Ms["theta_L"]
                tp_L = Mp["theta_L"]
                ts_L = Ms["theta_L"]
                facp = nc[len(self.d)-1]*np.cos(tp_L)/(nc[0]*np.cos(tp_i))
                facs = nc[len(self.d)-1]*np.cos(ts_L)/(nc[0]*np.cos(ts_i))
                rp = Mp["M21"]/Mp["M11"]
                rs = Ms["M21"]/Ms["M11"]
                
                ### Reflectivity for each polarization
                self.Reflectivity_p[j][i] = np.real(rp * np.conj(rp))
                self.Reflectivity_s[j][i] = np.real(rs * np.conj(rs))
                ### Transmissivity for each polarization
                self.Transmissivity_p[j][i] = np.real(tp*np.conj(tp)*facp)
                self.Transmissivity_s[j][i] = np.real(ts*np.conj(ts)*facs)
                ### Emissivity for each polarization
                self.Emissivity_p[j][i] = 1. - self.Reflectivity_p[j][i] - self.Transmissivity_p[j][i]
                self.Emissivity_s[j][i] = 1. - self.Reflectivity_s[j][i] - self.Transmissivity_s[j][i]
                
        return 1
    
    ### Method to evaluate/update thermal emission spectrum - normal angle only!
    ''' FLAGGED!  Rename method with accepted convention! '''
    def ThermalEmission(self):
        ### Temperature might change, update BB spectrum
        self.BBs = datalib.BB(self.lam, self.T)
        ### Emissivity doesn't change unless structure changes
        self.TE = self.BBs * self.Emissivity
        return 1
    
    ### Method to evaluate/update thermal emission spectrum
    ''' FLAGGED!  Rename method with accepted convention! '''
    def ThermalEmission_EA(self):
        
        ### Temperature might change, update BB spectrum
        self.BBs = datalib.BB(self.lam, self.T)
        #temp = np.zeros(len(self.lam))
        
        for i in range(0,len(self.t)):
            ### Thermal emission goes like BBs(lambda) * eps(theta, lambda) * cos(theta)
            for j in range(0,len(self.lam)):
                self.TE_p[i][j] = self.BBs[j] * self.Emissivity_p[i][j] * np.cos(self.t[i])
                self.TE_s[i][j] = self.BBs[j] * self.Emissivity_s[i][j] * np.cos(self.t[i])
            
        return 1
    
    ### METHODS FOR STPVLIB
    
    ### Normal versions first - no explicit dependence on angle
    
    ### Spectral Efficiency - see Eq. 4 in Jeon et al, Adv. Energy Mater. 2018 (8) 1801035
    def stpv_se(self):
        self.SE = stpvlib.SpectralEfficiency(self.TE, self.lam, self.lbg)
        return 1
    
    ### Power density - see Eq. 3 in Jeon et al, Adv. Energy Mater. 2018 (8) 1801035
    def stpv_pd(self):
        self.PD = stpvlib.Pwr_den(self.TE, self.lam, self.lbg)
        return 1
    
    ### TPV Efficiency, see Eq. S20-S26 in Jeon et al, Adv. Energy Mater. 2018 (8) 1801035
    def stpv_etatpv(self):
        self.ETATPV = stpvlib.Eta_TPV(self.TE, self.lam, self.PV, self.T_cell)
        return 1
    
    ### Explicit Angle versions of methods for STPV quantities
    def stpv_se_ea(self):
        self.SE = stpvlib.SpectralEfficiency_EA(self.TE_p, self.TE_s, self.lam, self.lbg, self.t, self.w)
    
        P_den = 0.
        P_inc = 0.
        dl = abs(self.lam[1] - self.lam[0])
        for i in range(0,len(self.w)):
            P_den_som = 0.
            P_inc_som = 0.
            for j in range(0,len(self.lam)):
                P_inc_som = P_inc_som + 0.5*self.TE_p[i][j]*dl
                P_inc_som = P_inc_som + 0.5*self.TE_s[i][j]*dl
                if self.lam[j]>=self.lbg:
                    P_den_som = P_den_som + 0.5*self.lam[j]/self.lbg*self.TE_p[i][j]*dl 
                    P_den_som = P_den_som + 0.5*self.lam[j]/self.lbg*self.TE_s[i][j]*dl
                
            P_den = P_den + self.w[i] * P_den_som
            P_inc = P_inc + self.w[i] * P_inc_som
        
        self.SE = P_den/P_inc
        return 1
        
        
    def stpv_pd_ea(self):
        self.PD = stpvlib.Pwr_den_EA(self.TE_p, self.TE_s, self.lam, self.lbg, self.t, self.w)
        return 1
    
    ''' FLAGGED! Need stpv_etatpv_ea method!!! '''
    
    
    ### Absorber Efficiency - see 
    def stpv_etaabs(self):
        alpha = stpvlib.absorbed_power_ea(self.lam, self.n, self.d, self.solarconc)
        beta = stpvlib.p_in(self.TE, self.lam)
        self.ETAABS = (alpha - beta)/alpha
        return 1
        
    def stpv_etaabs_ea(self):
        
        ### Power absorbed is going to explicitly consider a range of incident angles which
        ### will depend on the solar concentration
        alpha = stpvlib.absorbed_power_ea(self.lam, self.n, self.d, self.solarconc)
        beta = stpvlib.p_in_ea(self.TE_p, self.TE_s, self.lam, self.t, self.w )
        self.ETAABS = (alpha - beta)/alpha
        return 1

    ### Method to add a layer to the bottom of the structure
    ### and re-compute desired quantities
    def insert_layer(self, layer_number, material, thickness):
        ### just use numpy insert for thickness array
        new_d = np.insert(self.d, layer_number, thickness)
        ### because material names can have variable number of characters,
        ### insert may not reliably work... do "manually"
        new_m = []
        for i in range(0,layer_number):
            new_m.append(self.matlist[i])
        new_m.append(material)
        for i in range(layer_number+1,len(self.matlist)+1):
            new_m.append(self.matlist[i-1])
            
        print(new_m)
        ### de-allocate memory associated with self.d, self.matlist, self.n arrays
        self.d = None
        self.matlist = None
        self.n = None

        ### assign new values to self.d, self.matlist, self.n
        self.d = new_d
        self.matlist = new_m
  
        self.n = None 
        self.n = np.zeros((len(self.d),len(self.lam)),dtype=complex)
        for i in range(0,len(self.matlist)):
                self.n[:][i] = datalib.Material_RI(self.lam, self.matlist[i])
        
        ### in all cases, updated Fresnel quantities
        self.Fresnel()
        
        if (self.explicit_angle):
            
            self.Fresnel_EA()
        
        ### if a thermal application is requested, update Thermal Emission as well
        #if (self.stpv_emitter_calc or self.stpv_absorber_calc or self.cooling_calc or self.lightbulb_calc or self.color_calc):
        #    self.ThermalEmission()
        if self.stpv_emitter_calc:
            self.ThermalEmission()
            self.stpv_se()
            self.stpv_pd()
            self.stpv_etatpv()
            
            if (self.explicit_angle):
                self.ThermalEmission_EA()
                self.stpv_se_ea()
                self.stpv_pd_ea()
                ### need to implement eta_tpv_ea method.
                #self.stpv_etatpv_ea()
            
        if self.stpv_absorber_calc:
            self.ThermalEmission()
            
            if (self.explicit_angle):
                self.ThermalEmission_EA()
                self.stpv_etaabs()
            else:
                self.stpv_etaabs()
                
            
        
        
        return 1


        

    
    ### METHODS FOR COLORLIB
    
    ### displays the percieved color of an object at a specific temperature
    ### based only on thermal emission
    ''' FLAGGED!  Rename method with accepted convention! '''
    def ThermalColor(self):
        string = "Color at T = " + str(self.T) + " K"
        colorlib.RenderColor(self.TE, self.lam, string)
        return 1
    
    ### Displays the perceived color of an object based only
    ### on reflected light
    ''' FLAGGED!  Rename method with accepted convention! '''
    def AmbientColor(self):
        string = "Ambient Color"
        colorlib.RenderColor(self.Reflectivity, self.lam, string)
        return 1
    
    ### Displays the percieved color of a narrow bandwidth lightsource
    def pure_color(self, wl):
        Spectrum = np.zeros_like(self.lam)
        for i in range(0,len(Spectrum)):
            if abs(self.lam[i] - wl)<5e-9:
                Spectrum[i] = 1
        colorlib.RenderColor(Spectrum, self.lam, str(wl))
        return 1
    
    ### METHODS FOR LIGHTLIB
    ''' FLAGGED!  Rename method with accepted convention! '''
    def LuminousEfficiency(self):
        self.eta_lum = lightlib.Lum_efficiency(self.lam, self.TE)
        #print("just calculated eta_lum and it is ",self.eta_lum)
        return 1
    ''' FLAGGED!  Rename method with accepted convention! '''
    def LuminousEfficacy(self):
        self.lum_effic = self.eta_lum * 683
        return 1
        
    ### MISCELLANEOUS METHODS TO MANIPULATE THE STRUCTURE
    ### OR GATHER DATA ABOUT THE STRUCTURE
    
    ### Get the RI of a particular layer (at each wavelength specified by user)
    def layer_ri(self, layer):
        RI = np.zeros(len(self.lam),dtype=complex)
        for i in range(0,len(self.lam)):
            RI[i] = self.n[layer][i]
        return RI
    
    ### Define the RI of a specified layer to be an alloy
    ### between two specified materials, mat1 and mat2,
    ### using Bruggenmans approximation
    def layer_alloy(self, layer, fraction, mat1, mat2, model):
        ### Bruggeman model must be specified
        if (model=='Bruggeman'):
            ### Get RIs of two materials... mat1 can be 
            ### a string that codes a material name or 
            ### it can be a single number
            if(isinstance(mat1, str)):
                n_1 = datalib.Material_RI(self.lam, mat1)
            else:
                n_1 = mat1
                
            n_2 = datalib.Material_RI(self.lam, mat2)
            
            for i in range(0,len(self.lam)):
                if(isinstance(mat1, str)):
                    eps1 = n_1[i]*n_1[i]
                else:
                    eps1 = n_1*n_1
                    
                eps2 = n_2[i]*n_2[i]
                flag = 1
                f1 = (1-fraction)
                f2 = fraction
                b = (2*f1-f2)*eps1 + (2*f2 - f1)*eps2
                arg = 8*eps1*eps2 + b*b
                srarg = np.sqrt(arg)
                
                if (np.imag(arg)<0):
                    flag = -1
                else:
                    flag = 1
                    
                epsBG = (b+flag*srarg)/4.
                self.n[layer][i] = np.sqrt(epsBG)
        #### Default is Maxwell-Garnett        
        else:
            if(isinstance(mat1, str)):
                n_1 = datalib.Material_RI(self.lam, mat1)
            else:
                n_1 = mat1
                
            n_2 = datalib.Material_RI(self.lam, mat2)
            f = fraction
            

            for i in range(0,len(self.lam)):
                ### eps1 == epsD and eps2 == epsM in MG notation
                if(isinstance(mat1, str)):
                    epsD = n_1[i]*n_1[i]
                else:
                    epsD = n_1*n_1

                epsM = n_2[i]*n_2[i]
                num = epsD*(2*f*(epsM-epsD) + epsM + 2*epsD)
                denom = 2*epsD + epsM + f*(epsD-epsM)
                self.n[layer][i] = np.sqrt((num/denom))
                
        return 1
    
    #### Sets the refractive index for a specified layer
    #### to a single specified refractive index value
    ''' FLAGGED!  Rename method with accepted convention! '''
    def LayerStaticRI(self, layer, RI):
        for i in range(0,len(self.lam)):
            self.n[layer][i] = RI
            
        return 1
    
    ### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    ### THIS METHOD IS HIGHLY SPECIFIC FOR A PARTICULAR USE CASE AND SHOULD
    ### NOT BE INCLUDED IN THE PUBLIC RELEASE!!!!!
    def fitness(self):
        h=6.626e-34 #Js
        k=1.38064852e-23 #mmKg/ssK
        c=299792458 #m/s
        q = 1.60217662e-19 # Coulombs
        T_cell = 293.15+60
        ### bunch of parameters specific to the system
        lbg = 2254e-9
        ebg = h*c/lbg
        J0 = 1.5e5 * np.exp(-ebg/(k*T_cell))
        #EQE = 1.0
        EQE = 0.82
        FF = 0.55
        F = 0.85
        f = 1./2.
        beta  = 0.96
        sumN = 0.
        sumD = 0.
        Jsc = 0.
        
        ### here we have a linear lambda array
        dlambda = abs(self.lam[1]-self.lam[0])
        for i in range(0,len(self.lam)-1): #len(lam)-1):
            l = self.lam[i]
            ### note the factor of pi... this assumes emissivity does not depend on angle
            sumD = sumD + np.pi*self.TE[i] * dlambda
            ### accumulate sum for numerator if lambda<lambda_b
            if l<=lbg:
                sumN = sumN + l/lbg * np.pi*self.TE[i] * dlambda
                ### accumulate Jsc sum if lambda is within the bandwidth
                ### suggested by Qiu et al.
                if l>=(lbg/2.5):
                    Jsc = Jsc + F * np.pi*self.TE[i] * (EQE * q * l/(h*c)) * dlambda
                    
        if (Jsc>J0):
            Voc = k*T_cell * np.log(Jsc/J0) / q
            red_v = q*Voc/(k*T_cell)
            FF = beta * (red_v - np.log(red_v + 0.72))/(red_v + 1)
            eta_tpv = (Voc * Jsc * FF)/sumD
            
        else:
            eta_tpv = 0.
            
        eta_s = sumN / sumD
        self.SE = eta_s
        self.PD = sumN
        self.ETATPV = eta_tpv
        return 1

    
    ### METHODS FOR PLOTTING DATA!
    
    ### Plot thermal emission
    def plot_te(self):
        plt.plot(self.lam*1e9, self.TE, 'red')
        string = "Thermal Emission at " + str(self.T) + " K"
        plt.legend(string)
        plt.show()
        return 1
    
    ### Plot reflectivity
    def plot_reflectivity(self):
        plt.plot(self.lam*1e9, self.Reflectivity, 'red')
        string = "Reflectivity"
        plt.legend(string)
        plt.show()
        return 1
    
    ### Plot emissivity
    def plot_emissivity(self):
        plt.plot(self.lam*1e9, self.Emissivity, 'blue')
        string = "Emissivity"
        plt.legend(("Emissivity"))
        plt.show()
        return 1   
    
    ### RESONANCE METHODS
    
    ### Find SPP mode for a structure at a particular
    ### wavelength that has index idx in the array of wavelengths!

    def find_spp(self, idx):
        ### get wavevector at idx'th wavelength
        k0 = np.pi*2/self.lam[idx]
        L = len(self.d)
        ### array of RIs for the structure at the idx'th wavelength
        nc = np.zeros(L,dtype=complex)
        for j in range(0,L):
            nc[j] = self.n[j][idx]
            
        ### SPP is "above the light line" so
        ### start searching beta at the light line
        b_beg = k0*nc[L-1]
        ### set maximum beta as k0*index of incident material
        b_end = k0*nc[0]
        
        ### alpha is harder to bound... must be positive, should be much smaller
        ### than beta
        a_beg = 0.000001
        a_end = 0.2*b_end
        
        beta = np.linspace(b_beg, b_end,100)
        alpha = np.linspace(a_beg, a_end, 100)
        
        ### initialize values
        rr_max = -100
        rr_temp = 0
        a_spp = 0
        b_spp = 0

        for a in alpha:
           # print(" ")
            for b in beta:
                kx = b + a*1j
                rr_temp = tmm.tmm_ab(k0, kx, 'p', nc, self.d)                
                #print(np.real(kx),np.imag(kx), t_temp)
                #t_array[k] = t_temp
                #k+=1
                if rr_temp>rr_max:
                    rr_max = rr_temp
                    a_spp = a
                    b_spp = b

        self.SPP_Resonance = b_spp+a_spp*1j
        return 1

    def find_pa(self, idx):
        ### get wavevector at idx'th wavelength
        k0 = np.pi*2/self.lam[idx]
        L = len(self.d)
        ### array of RIs for the structure at the idx'th wavelength
        nc = np.zeros(L,dtype=complex)
        for j in range(0,L):
            nc[j] = self.n[j][idx]
            
        ### SPP is "above the light line" so
        ### start searching beta at the light line
        b_beg = k0*nc[L-1]
        ### set maximum beta as k0*index of incident material
        b_end = k0*nc[0]
        
        ### alpha is harder to bound... must be positive, should be much smaller
        ### than beta
        a_beg = 0.000001
        a_end = 0.2*b_end
        
        beta = np.linspace(b_beg, b_end,100)
        alpha = np.linspace(a_beg, a_end, 100)
        
        ### initialize values
        rr_min = 100
        rr_temp = 0
        a_spp = 0
        b_spp = 0

        for a in alpha:
           # print(" ")
            for b in beta:
                kx = b + a*1j
                rr_temp = tmm.tmm_ab(k0, kx, 'p', nc, self.d)                
                #print(np.real(kx),np.imag(kx), t_temp)
                #t_array[k] = t_temp
                #k+=1
                if rr_temp<rr_min:
                    rr_min = rr_temp
                    a_spp = a
                    b_spp = b

        self.PA_Resonance = b_spp+a_spp*1j
        return 1


    ### The goal of this method is to allow the user to interactively
    ### specify the structure as painlessly as possible.
    ### They will supply an array of thicnesses
    ### then an array of materials (we should tell them which are supported!)
    ### and then they will specify the range of wavelengths they 
    ### wish to consider
    ### The result will be an array of wavelengths, an array of thicknesses
    ### that define the geometry, and array of RI values at each wavelegnth
    ### that defines the structure
    def interactive_structure(self):
        print(" Enter list of thicknesses for structure ")
        self.d = [float(x) for x in input().split()]
        print(" Enter list of materials for each layer ")
        self.matlist = [str(x) for x in input().split()]
        print(" Enter range of wavelength in the following order: ")
        print(" starting_wl  ending_wl  number_of_wl ")
        ### I don't think lamlist needs to be an attribute
        lamlist = [float(x) for x in input().split()]
        self.lam = np.linspace(lamlist[0],lamlist[1],int(lamlist[2]))
        self.n = np.zeros((len(self.d),len(self.lam)),dtype=complex)
        for i in range(0,len(self.matlist)):
            self.n[:][i] = datalib.Material_RI(self.lam, self.matlist[i])
        print(" Enter temperature of your structure")
        self.T = float(input())
        print(" The next questions relate to the quantities you would like to compute ")
        print(" By default, the far-field transmission, reflection, and absorption/emissivity")
        print(" spectra will be computed... all other quantities must be selected")
        print(" To compute STPV-related quantities, type 'Y'")
        choice = input()
        if choice=='Y' or choice=='y' or choice=='Yes' or choice=='yes' or choice=='YES':
            self.stpv_calc = 1
        print(" To compute Cooling-related quantities, type 'Y'")
        choice = input()
        if choice=='Y' or choice=='y' or choice=='Yes' or choice=='yes' or choice=='YES':
            self.cooling_calc = 1
        print(" To compute Lightbulb-related quantities, type 'Y'")
        choice = input()
        if choice=='Y' or choice=='y' or choice=='Yes' or choice=='yes' or choice=='YES':
            self.lightbulb_calc = 1
        print(" To compute color-related quantities, type 'Y'")
        choice = input()
        if choice=='Y' or choice=='y' or choice=='Yes' or choice=='yes' or choice=='YES':
            self.color_calc = 1
     
        return 1
    
    ### The goal of this method is to allow the user to run a calculation 
    ### using an input file
    def batch_structure(self,inputfile):
        ### set default values for attributes:
        self.d = [0, 100e-9, 0]
        self.matlist = ['Air', 'W', 'Air']
        self.lamlist = [400e-9, 800e-9, 200]
        self.T = 300
        ### now read input file and replace defaults if specified
        with open(inputfile,"r") as f:
            data = f.readlines()
            
            for line in data:
                words = line.split()
                if (words[0]=='Thickness_List'):
                    self.d = [float(words[1]), float(words[2]), float(words[3])]
                if (words[0]=='Material_List'):
                    self.matlist = [words[1], words[2], words[3]]
                if (words[0]=='Lambda_List'):
                    self.lamlist = [float(words[1]), float(words[2]), float(words[3])]
                if (words[0]=='Temperature'):
                    self.T = float(words[1])
                if (words[0]=='STPV'):
                    self.stpv_calc = 1
                if (words[0]=='COOLING'):
                    self.cooling_calc = 1
                if (words[0]=='LIGHTBULB'):
                    self.lighbulb_calc = 1
                if (words[0]=='COLOR'):
                    self.color_calc = 1
                
                self.lam = np.linspace(self.lamlist[0],self.lamlist[1],int(self.lamlist[2]))
                self.n = np.zeros((len(self.d),len(self.lam)),dtype=complex)
                for i in range(0,len(self.matlist)):
                    self.n[:][i] = datalib.Material_RI(self.lam, self.matlist[i])
                

        return 1
    
    def inline_structure(self, args):
        if 'Lambda_List' in args:
            lamlist = args['Lambda_List']
            self.lam = np.linspace(lamlist[0],lamlist[1],int(lamlist[2]))
        else:
            print(" Lambda array not specified! ")
            print(" Choosing default array of 1000 wl between 400 and 6000 nm")
            self.lam = np.linspace(400e-9,6000e-9,1000)

        
        if 'Thickness_List' in args:
            self.d = args['Thickness_List']
        ### default structure
        else:
            print("  Thickness array not specified!")
            print("  Proceeding with default structure - optically thick W! ")
            self.d = [0, 900e-9, 0]
            self.matlist = ['Air', 'W', 'Air']
            self.n = np.zeros((len(self.d),len(self.lam)),dtype=complex)
            for i in range(0,len(self.matlist)):
                self.n[:][i] = datalib.Material_RI(self.lam, self.matlist[i])
                
        if 'Material_List' in args:
            self.matlist = args['Material_List']
            self.n = np.zeros((len(self.d),len(self.lam)),dtype=complex)
            for i in range(0,len(self.matlist)):
                    self.n[:][i] = datalib.Material_RI(self.lam, self.matlist[i])
            
        else:
            print("  Material array not specified!")
            print("  Proceeding with default structure - optically thick W! ")
            self.d = [0, 900e-9, 0]
            self.matlist = ['Air', 'W', 'Air']
            self.n = np.zeros((len(self.d),len(self.lam)),dtype=complex)
            for i in range(0,len(self.matlist)):
                    self.n[:][i] = datalib.Material_RI(self.lam, self.matlist[i])

        if 'Temperature' in args:
            self.T = args['Temperature']
        else:
            print(" Temperature not specified!")
            print(" Proceeding with default T = 1200 K")
            self.T = 1200
        
        ### Check to see what calculations should be done!
        if 'STPV_EMIT' in args:
            self.stpv_emitter_calc = args['STPV_EMIT']
        else:
            self.stpv_emitter_calc = 0
        if 'STPV_ABS' in args:
            self.stpv_absorber_calc = args['STPV_ABS']
        else:
            self.stpv_absorber_calc = 0
        if 'COOLING' in args:
            self.cooling_calc = args['COOLING']
        else:
            self.cooling_calc = 0
        if 'LIGHTBULB' in args:
            self.lightbulb_calc = args['LIGHTBULB']
        else:
            self.lightbulb_calc = 0
        if 'COLOR' in args:
            self.color_calc = args['COLOR']
        else:
            self.color_calc = 0
        if 'EXPLICIT_ANGLE' in args:
            self.explicit_angle = args['EXPLICIT_ANGLE']
        else:
            self.explicit_angle = 0
        if 'DEG' in args:
            self.deg = args['DEG']
        else:
            self.deg = 7
            
        return 1

    
