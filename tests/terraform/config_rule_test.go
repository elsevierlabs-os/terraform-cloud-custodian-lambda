package test

import (
	"fmt"
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestConfigRuleExample(t *testing.T) {

	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../../examples/config-rule",
	})

	defer terraform.Destroy(t, terraformOptions)

	terraform.InitAndApply(t, terraformOptions)

	lambdaFunctionName := terraform.Output(t, terraformOptions, "lambda_function_name")
	assert.Equal(t, "custodian-dev-config-rule", lambdaFunctionName, "lambda_function_name is not correct")

	modeType := terraform.Output(t, terraformOptions, "mode_type")
	assert.Equal(t, "config-rule", modeType, "mode_type is not correct")

	configRule := terraform.OutputMap(t, terraformOptions, "config_rule")
	assert.NotEmpty(t, configRule, "config_rule should not be empty")

	description := configRule["description"]
	assert.NotEmpty(t, description, "config_rule should have a description")
	assert.Equal(t, "cloud-custodian lambda policy", description, "config_rule description is not correct")

	scope := configRule["scope"]
	assert.NotEmpty(t, scope, "config_rule should have a scope defined")
	assert.Contains(t, scope, "AWS::EC2::", "config_rule scope is not correct")

	source := configRule["source"]
	assert.NotEmpty(t, source, "config_rule should have a source defined")
	sourceStr := fmt.Sprintf("%v", source)
	assert.Contains(t, sourceStr, "CUSTOM_LAMBDA", "config_rule source owner is not correct")
	lambdaArn := terraform.Output(t, terraformOptions, "lambda_function_arn")
	assert.Contains(t, sourceStr, lambdaArn, "config_rule source identifier is not correct")
	assert.Contains(t, sourceStr, "aws.config", "config_rule source event source is not correct")
	assert.Contains(t, sourceStr, "ConfigurationItemChangeNotification", "config_rule trigger is not correct")

	maxExecFreq := configRule["maximum_execution_frequency"]
	if maxExecFreq != "" {
		validFrequencies := []string{"One_Hour", "Three_Hours", "Six_Hours", "Twelve_Hours", "TwentyFour_Hours"}
		found := false
		for _, freq := range validFrequencies {
			if maxExecFreq == freq {
				found = true
				break
			}
		}
		assert.True(t, found, "config_rule maximum_execution_frequency should be a valid AWS Config frequency value")
	}
}
