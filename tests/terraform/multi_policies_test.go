package test

import (
	"sort"
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestMultiPolicies(t *testing.T) {

	t.Parallel()

	expectedRegions := []string{"eu-west-1", "us-east-1", "us-east-2"}

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/multi-policies",
		Vars: map[string]interface{}{
			"regions":                       expectedRegions,
			"create_multi_policies_s3_bucket": false,
		},
	})

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)

	policyNames := terraform.OutputList(t, terraformOptions, "policy_names")

	assert.NotEmpty(t, policyNames, "Should have at least one policy")

	regionsOutput := getOutputMapOfStringLists(t, terraformOptions, "regions")
	for _, policyName := range policyNames {
		// Get regions for this policy and sort for comparison
		regionsForPolicy := regionsOutput[policyName]
		sort.Strings(regionsForPolicy)

		assert.Equal(t, expectedRegions, regionsForPolicy,
			"Policy %s should be deployed to all expected regions", policyName)
	}
}
