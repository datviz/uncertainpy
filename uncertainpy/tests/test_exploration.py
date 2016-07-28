import os
import unittest
import subprocess
import shutil
import chaospy as cp


from uncertainpy import UncertaintyEstimations, Parameters
from uncertainpy.features import TestingFeatures
from uncertainpy.models import TestingModel1d


class TestPlotUncertainpy(unittest.TestCase):
    def setUp(self):
        self.folder = os.path.dirname(os.path.realpath(__file__))

        self.test_data_dir = os.path.join(self.folder, "data")
        self.output_test_dir = ".tests/"

        if os.path.isdir(self.output_test_dir):
            shutil.rmtree(self.output_test_dir)
        os.makedirs(self.output_test_dir)

        percentages = [0.01, 0.03, 0.05]

        self.test_distributions = {"uniform": percentages}
        self.seed = 10


        def mock_distribution(x):
            return cp.Uniform(0, 1)

        parameterlist = [["a", 1, mock_distribution],
                         ["b", 2, mock_distribution]]

        parameters = Parameters(parameterlist)
        model = TestingModel1d(parameters)

        self.uncertainty = UncertaintyEstimations(model,
                                                  features=TestingFeatures(),
                                                  feature_list="all",
                                                  verbose_level="error",
                                                  output_dir_data=self.output_test_dir,
                                                  output_dir_figures=self.output_test_dir,
                                                  nr_mc_samples=10**1,
                                                  seed=self.seed)

    # def tearDown(self):
    #     if os.path.isdir(self.output_test_dir):
    #         shutil.rmtree(self.output_test_dir)
    #
    #
    # def test_init(self):
    #     self.uncertainty = UncertaintyEstimations(TestingModel1d(),
    #                                               features=TestingFeatures(),
    #                                               feature_list="all",
    #                                               verbose_level="error",
    #                                               output_dir_data=self.output_test_dir,
    #                                               output_dir_figures=self.output_test_dir,
    #                                               nr_mc_samples=10**1,
    #                                               seed=self.seed)
    #
    #
    #
    #     self.assertIsInstance(self.uncertainty, UncertaintyEstimations)
    #
    #
    # def test_exploreParameters(self):
    #     self.uncertainty.exploreParameters(self.test_distributions)
    #
    #     self.assert_files_in_folder("uniform_0.01")
    #     self.assert_files_in_folder("uniform_0.03")
    #     self.assert_files_in_folder("uniform_0.05")



    def assert_files_in_folder(self, folder):
        self.assertTrue(os.path.isdir(os.path.join(self.output_test_dir,
                                                   folder)))

        self.assertTrue(os.path.isfile(os.path.join(self.output_test_dir,
                                                    folder,
                                                    "TestingModel1d")))
        self.assertTrue(os.path.isfile(os.path.join(self.output_test_dir,
                                                    folder,
                                                    "TestingModel1d_single-parameter-a")))

        self.assertTrue(os.path.isfile(os.path.join(self.output_test_dir,
                                                    folder,
                                                    "TestingModel1d_single-parameter-b")))


    def test_compareMC(self):
        mc_samples = [10, 100]

        self.uncertainty.compareMC(mc_samples)

        compare_file = os.path.join(self.folder, "data/pc",
                                    "TestingModel1d")
        data_file = os.path.join(self.output_test_dir, "pc/TestingModel1d")
        result = subprocess.call(["h5diff", data_file, compare_file])


        self.assertEqual(result, 0)

        compare_file = os.path.join(self.folder, "data/mc_10",
                                    "TestingModel1d")
        data_file = os.path.join(self.output_test_dir, "mc_10/TestingModel1d")
        result = subprocess.call(["h5diff", data_file, compare_file])

        self.assertEqual(result, 0)

        compare_file = os.path.join(self.folder, "data/mc_100",
                                    "TestingModel1d")
        data_file = os.path.join(self.output_test_dir, "mc_100/TestingModel1d")
        result = subprocess.call(["h5diff", data_file, compare_file])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()