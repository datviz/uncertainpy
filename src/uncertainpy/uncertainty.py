import os
import types
import multiprocess as mp

from .core.uncertainty_calculations import UncertaintyCalculations
from .plotting.plot_uncertainty import PlotUncertainty
from .utils import create_logger
from .data import Data
from .core.base import ParameterBase


#  Figures are always saved on the format:
#  output_dir_figures/parameter_value-that-is-plotted.figure-extension

class UncertaintyQuantification(ParameterBase):
    def __init__(self,
                 model,
                 parameters,
                 features=None,
                 uncertainty_calculations=None,
                 save_figures=True,
                 output_dir_figures="figures/",
                 figureformat=".png",
                 save_data=True,
                 output_dir_data="data/",
                 verbose_level="info",
                 verbose_filename=None,
                 create_PCE_custom=None,
                 CPUs=mp.cpu_count(),
                 suppress_model_graphics=True,
                 p=3,
                 nr_pc_samples=None,
                 nr_mc_samples=10*3,
                 nr_pc_mc_samples=10*5,
                 seed=None,
                 allow_incomplete=False):


        if uncertainty_calculations is None:
            self._uncertainty_calculations = UncertaintyCalculations(
                model=model,
                parameters=parameters,
                features=features,
                CPUs=CPUs,
                suppress_model_graphics=suppress_model_graphics,
                p=p,
                nr_pc_samples=nr_pc_samples,
                nr_mc_samples=nr_mc_samples,
                nr_pc_mc_samples=nr_pc_mc_samples,
                seed=seed,
                verbose_level=verbose_level,
                verbose_filename=verbose_filename,
                allow_incomplete=allow_incomplete
            )
        else:
            self._uncertainty_calculations = uncertainty_calculations

        super(UncertaintyQuantification, self).__init__(parameters=parameters,
                                                    model=model,
                                                    features=features,
                                                    verbose_level=verbose_level,
                                                    verbose_filename=verbose_filename)



        self.data = None

        self.save_figures = save_figures
        self.save_data = save_data
        self.output_dir_data = output_dir_data
        self.output_dir_figures = output_dir_figures

        self.logger = create_logger(verbose_level,
                                    verbose_filename,
                                    self.__class__.__name__)

        if create_PCE_custom is not None:
            self.uncertainty_calculations.create_PCE_custom = types.MethodType(create_PCE_custom,
                                                                               self.uncertainty_calculations)




        self.plotting = PlotUncertainty(output_dir=self.output_dir_figures,
                                        figureformat=figureformat,
                                        verbose_level=verbose_level,
                                        verbose_filename=verbose_filename)


    @ParameterBase.features.setter
    def features(self, new_features):
        ParameterBase.features.fset(self, new_features)

        self.uncertainty_calculations.features = self.features


    @ParameterBase.model.setter
    def model(self, new_model):
        ParameterBase.model.fset(self, new_model)

        self.uncertainty_calculations.model = self.model


    @ParameterBase.parameters.setter
    def parameters(self, new_parameters):
        ParameterBase.parameters.fset(self, new_parameters)

        self.uncertainty_calculations.parameters = self.parameters


    @property
    def uncertainty_calculations(self):
        return self._uncertainty_calculations


    @uncertainty_calculations.setter
    def uncertainty_calculations(self, new_uncertainty_calculations):
        self._uncertainty_calculations = new_uncertainty_calculations

        self.uncertainty_calculations.features = self.features
        self.uncertainty_calculations.model = self.model


    # TODO add features_to_run as argument to this function
    # TODO make sure which arguments are sent to this function and wich arguments
    #  to UncertaintyQuantification makes sense
    def quantify(self,
                 method="pc",
                 pc_method="regression",
                 rosenblatt=False,
                 uncertain_parameters=None,
                 single=False,
                 plot_condensed=True,
                 plot_results=False,
                 output_dir_figures=None,
                 output_dir_data=None,
                 filename=None,
                 sensitivity="sensitivity_1",
                 **custom_kwargs):
        """
method: pc, mc
pc_method: "regression"
        """
        uncertain_parameters = self.uncertainty_calculations.convert_uncertain_parameters(uncertain_parameters)


        if method.lower() == "pc":
            if single:
                self.polynomial_chaos_single(uncertain_parameters=uncertain_parameters,
                                             method=pc_method,
                                             rosenblatt=rosenblatt,
                                             plot_condensed=plot_condensed,
                                             plot_results=plot_results,
                                             output_dir_figures=output_dir_figures,
                                             output_dir_data=output_dir_data,
                                             filename=filename)
            else:
                self.polynomial_chaos(uncertain_parameters=uncertain_parameters,
                                      method=pc_method,
                                      rosenblatt=rosenblatt,
                                      plot_condensed=plot_condensed,
                                      plot_results=plot_results,
                                      output_dir_figures=output_dir_figures,
                                      output_dir_data=output_dir_data,
                                      filename=filename,
                                      sensitivity=sensitivity)
        elif method.lower() == "mc":
            if single:
                self.monte_carlo_single(uncertain_parameters=uncertain_parameters,
                                        plot_condensed=plot_condensed,
                                        plot_results=plot_results,
                                        output_dir_figures=output_dir_figures,
                                        output_dir_data=output_dir_data,
                                        filename=filename)
            else:
                self.monte_carlo(uncertain_parameters=uncertain_parameters,
                                 plot_condensed=plot_condensed,
                                 plot_results=plot_results,
                                 output_dir_figures=output_dir_figures,
                                 output_dir_data=output_dir_data,
                                 filename=filename)

        elif method.lower() == "custom":
            self.custom_uncertainty_quantification(plot_condensed=plot_condensed,
                                                   plot_results=plot_results,
                                                   output_dir_figures=output_dir_figures,
                                                   output_dir_data=output_dir_data,
                                                   filename=filename,
                                                   **custom_kwargs)



    def custom_uncertainty_quantification(self,
                                          plot_condensed=True,
                                          plot_results=False,
                                          output_dir_figures=None,
                                          output_dir_data=None,
                                          filename=None,
                                          **custom_kwargs):


        self.data = self.uncertainty_calculations.custom_uncertainty_quantification(**custom_kwargs)

        if self.save_data:
            if filename is None:
                filename = self.model.name

            self.save(filename, output_dir=output_dir_data)


        if self.save_figures:
            self.plot(condensed=plot_condensed,
                      sensitivity=None,
                      output_dir=output_dir_figures)

        if plot_results:
            self.plot(results=True, output_dir=output_dir_figures)



    def polynomial_chaos(self,
                         uncertain_parameters=None,
                         method="regression",
                         rosenblatt=False,
                         plot_condensed=True,
                         plot_results=False,
                         output_dir_figures=None,
                         output_dir_data=None,
                         sensitivity="sensitivity_1",
                         filename=None):

        uncertain_parameters = self.uncertainty_calculations.convert_uncertain_parameters(uncertain_parameters)

        if len(uncertain_parameters) > 20:
            raise RuntimeWarning("The number of uncertain parameters is high."
                                 + "A Monte-Carlo method _might_ be faster.")


        self.data = self.uncertainty_calculations.polynomial_chaos(
            uncertain_parameters=uncertain_parameters,
            method=method,
            rosenblatt=rosenblatt
        )

        if self.save_data:
            if filename is None:
                filename = self.model.name

            self.save(filename, output_dir=output_dir_data)

        if self.save_figures:
            self.plot(condensed=plot_condensed, output_dir=output_dir_figures, sensitivity=sensitivity)

        if plot_results:
            self.plot(results=True, output_dir=output_dir_figures)



    def monte_carlo(self,
                    uncertain_parameters=None,
                    plot_condensed=True,
                    plot_results=False,
                    output_dir_figures=None,
                    output_dir_data=None,
                    filename=None):

        uncertain_parameters = self.uncertainty_calculations.convert_uncertain_parameters(uncertain_parameters)

        self.data = self.uncertainty_calculations.monte_carlo(uncertain_parameters=uncertain_parameters)

        if self.save_data:
            if filename is None:
                filename = self.model.name

            self.save(filename, output_dir=output_dir_data)


        if self.save_figures:
            self.plot(condensed=plot_condensed,
                      sensitivity=None,
                      output_dir=output_dir_figures)

        if plot_results:
            self.plot(results=True, output_dir=output_dir_figures)





    def polynomial_chaos_single(self,
                                uncertain_parameters=None,
                                method="regression",
                                rosenblatt=False,
                                plot_condensed=True,
                                plot_results=False,
                                output_dir_data=None,
                                output_dir_figures=None,
                                filename=None):

        uncertain_parameters = self.uncertainty_calculations.convert_uncertain_parameters(uncertain_parameters)

        if len(uncertain_parameters) > 20:
            raise RuntimeWarning("The number of uncertain parameters is high. "
                                 + "A Monte-Carlo method might be faster.")

        if filename is None:
            filename = self.model.name


        for uncertain_parameter in uncertain_parameters:
            self.logger.info("Running for " + uncertain_parameter)

            self.data = self.uncertainty_calculations.polynomial_chaos(
                uncertain_parameters=uncertain_parameter,
                method=method,
                rosenblatt=rosenblatt
            )

            tmp_filename = "{}_single-parameter-{}".format(
                filename,
                uncertain_parameter
            )

            if self.save_data:
                self.save(tmp_filename, output_dir=output_dir_data)


            if output_dir_figures is None:
                tmp_output_dir_figures = os.path.join(self.output_dir_figures, tmp_filename)
            else:
                tmp_output_dir_figures = os.path.join(output_dir_figures, tmp_filename)


            if self.save_figures:
                self.plot(condensed=plot_condensed,
                          sensitivity=None,
                          output_dir=tmp_output_dir_figures)

            if plot_results:
                self.plot(results=True,
                          output_dir=tmp_output_dir_figures)


    def monte_carlo_single(self,
                           uncertain_parameters=None,
                           plot_condensed=True,
                           plot_results=False,
                           output_dir_data=None,
                           output_dir_figures=None,
                           filename=None):
        uncertain_parameters = self.uncertainty_calculations.convert_uncertain_parameters(uncertain_parameters)

        if filename is None:
            filename = self.model.name


        for uncertain_parameter in uncertain_parameters:
            self.logger.info("Running MC for " + uncertain_parameter)

            self.data = self.uncertainty_calculations.monte_carlo(uncertain_parameter)

            tmp_filename = "{}_single-parameter-{}".format(
                filename,
                uncertain_parameter
            )

            if self.save_data:
                self.save(tmp_filename, output_dir=output_dir_data)


            if output_dir_figures is None:
                tmp_output_dir_figures = os.path.join(self.output_dir_figures, tmp_filename)
            else:
                tmp_output_dir_figures = os.path.join(output_dir_figures, tmp_filename)

            if self.save_figures:
                self.plot(condensed=plot_condensed, output_dir=tmp_output_dir_figures)

            if plot_results:
                self.plot(results=True, output_dir=tmp_output_dir_figures)



    def save(self, filename, output_dir=None):
        if output_dir is None:
            output_dir = self.output_dir_data

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        save_path = os.path.join(output_dir, filename + ".h5")

        self.logger.info("Saving data as: {}".format(save_path))

        ### TODO expand the save funcition to also save parameters and model information
        self.data.save(save_path)



    def load(self, filename):
        self.data = Data(filename)


    def plot(self,
             condensed=True,
             sensitivity="sensitivity_1",
             results=False,
             output_dir=None):

        if output_dir is None:
            output_dir = self.output_dir_figures


        self.plotting.data = self.data
        self.plotting.output_dir = output_dir

        if results:
            self.plotting.all_results()
        else:
            self.plotting.plot(condensed=condensed,
                               sensitivity=sensitivity)



    # def convert_uncertain_parameters(self, uncertain_parameters):
    #     if uncertain_parameters is None:
    #         uncertain_parameters = self.parameters.get_from_uncertain("name")

    #     if isinstance(uncertain_parameters, str):
    #         uncertain_parameters = [uncertain_parameters]

    #     return uncertain_parameters
